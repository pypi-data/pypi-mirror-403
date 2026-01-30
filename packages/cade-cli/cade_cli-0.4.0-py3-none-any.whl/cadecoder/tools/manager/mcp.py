"""MCP (Model Context Protocol) tool manager with OAuth 2.1 support."""

import asyncio
import json
import os
import re
import uuid
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode, urlparse

import httpx

from cadecoder.core.logging import log
from cadecoder.tools.manager.base import ToolAuthorizationRequired, ToolManager
from cadecoder.tools.manager.config import (
    MCPAuthType,
    MCPOAuthTokens,
    MCPServerConfig,
    MCPServerStore,
    MCPTransportType,
)


class StdioMCPConnection:
    """Manages stdio subprocess for MCP server."""

    def __init__(
        self, command: str, args: list[str] | None = None, env: dict[str, str] | None = None
    ):
        self.command = command
        self.args = args or []
        self.env = env
        self.process: asyncio.subprocess.Process | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the stdio subprocess."""
        if self.process:
            return

        full_env = os.environ.copy()
        if self.env:
            full_env.update(self.env)

        log.debug(f"Starting stdio MCP server: {self.command} {' '.join(self.args)}")

        self.process = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=full_env,
        )

        # Start stderr logger task
        asyncio.create_task(self._log_stderr())

    async def _log_stderr(self) -> None:
        """Log stderr output from subprocess."""
        if not self.process or not self.process.stderr:
            return

        try:
            async for line in self.process.stderr:
                log.debug(f"[stdio] {line.decode().rstrip()}")
        except Exception:
            pass

    async def send_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send JSON-RPC request via stdio."""
        async with self._lock:
            if not self.process or not self.process.stdin or not self.process.stdout:
                raise Exception("Process not started")

            # Write request
            line = json.dumps(request) + "\n"
            self.process.stdin.write(line.encode())
            await self.process.stdin.drain()

            # Read response
            response_line = await self.process.stdout.readline()
            if not response_line:
                raise Exception("Process closed unexpectedly")

            return json.loads(response_line)

    async def close(self) -> None:
        """Close the subprocess."""
        if self.process:
            if self.process.stdin:
                self.process.stdin.close()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except TimeoutError:
                log.warning("Stdio process did not terminate gracefully, killing...")
                self.process.kill()
                await self.process.wait()
            self.process = None


class MCPOAuthHandler:
    """Handles OAuth 2.1 authorization for MCP servers per MCP spec."""

    def __init__(self, server_config: MCPServerConfig) -> None:
        self.config = server_config
        self._client: httpx.AsyncClient | None = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client exists."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        return self._client

    def parse_www_authenticate(self, header: str) -> dict[str, str]:
        """Parse WWW-Authenticate header to extract OAuth parameters."""
        params: dict[str, str] = {}
        if header.lower().startswith("bearer "):
            header = header[7:]

        pattern = r'(\w+)="([^"]*)"'
        for match in re.finditer(pattern, header):
            params[match.group(1)] = match.group(2)

        return params

    async def discover_from_401(self, response: httpx.Response) -> tuple[str | None, str | None]:
        """Discover authorization server from 401 response."""
        www_auth = response.headers.get("WWW-Authenticate", "")
        params = self.parse_www_authenticate(www_auth)
        return params.get("resource_metadata"), params.get("scope")

    async def fetch_protected_resource_metadata(
        self, metadata_url: str | None = None
    ) -> dict[str, Any] | None:
        """Fetch Protected Resource Metadata per RFC 9728."""
        client = await self._ensure_client()
        parsed = urlparse(self.config.url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        urls_to_try = []
        if metadata_url:
            urls_to_try.append(metadata_url)

        if parsed.path and parsed.path != "/":
            path = parsed.path.rstrip("/")
            urls_to_try.append(f"{base}/.well-known/oauth-protected-resource{path}")

        urls_to_try.append(f"{base}/.well-known/oauth-protected-resource")

        for url in urls_to_try:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
            except Exception:
                continue

        return None

    async def fetch_authorization_server_metadata(self, issuer: str) -> dict[str, Any] | None:
        """Fetch Authorization Server Metadata per RFC 8414."""
        client = await self._ensure_client()
        parsed = urlparse(issuer)
        base = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path.rstrip("/") if parsed.path else ""

        urls_to_try = []
        if path:
            urls_to_try.extend(
                [
                    f"{base}/.well-known/oauth-authorization-server{path}",
                    f"{base}/.well-known/openid-configuration{path}",
                    f"{base}{path}/.well-known/openid-configuration",
                ]
            )
        else:
            urls_to_try.extend(
                [
                    f"{base}/.well-known/oauth-authorization-server",
                    f"{base}/.well-known/openid-configuration",
                ]
            )

        for url in urls_to_try:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    metadata = resp.json()
                    if "code_challenge_methods_supported" not in metadata:
                        log.warning(f"Auth server {url} doesn't advertise PKCE support")
                    return metadata
            except Exception:
                continue

        return None

    def generate_pkce(self) -> tuple[str, str]:
        """Generate PKCE code_verifier and code_challenge (S256)."""
        import base64
        import hashlib
        import secrets

        code_verifier = secrets.token_urlsafe(32)
        digest = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

        return code_verifier, code_challenge

    async def start_oauth_flow(
        self,
        auth_server_metadata: dict[str, Any],
        scope: str | None = None,
        client_id: str | None = None,
    ) -> tuple[str, str, str]:
        """Start OAuth authorization flow. Returns (auth_url, code_verifier, state)."""
        import secrets

        auth_endpoint = auth_server_metadata.get("authorization_endpoint")
        if not auth_endpoint:
            raise Exception("No authorization_endpoint in auth server metadata")

        code_verifier, code_challenge = self.generate_pkce()
        state = secrets.token_urlsafe(16)

        if not client_id:
            client_id = self.config.oauth_client_id or f"cade-mcp-{self.config.name}"

        if not scope:
            scope = " ".join(self.config.oauth_scopes or [])
            if not scope:
                supported = auth_server_metadata.get("scopes_supported", [])
                scope = " ".join(supported) if supported else ""

        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": "http://127.0.0.1:9876/callback",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": state,
            "resource": self.config.url,
        }
        if scope:
            params["scope"] = scope

        auth_url = f"{auth_endpoint}?{urlencode(params)}"
        return auth_url, code_verifier, state

    async def exchange_code_for_tokens(
        self,
        auth_server_metadata: dict[str, Any],
        code: str,
        code_verifier: str,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> MCPOAuthTokens:
        """Exchange authorization code for tokens."""
        client = await self._ensure_client()

        token_endpoint = auth_server_metadata.get("token_endpoint")
        if not token_endpoint:
            raise Exception("No token_endpoint in auth server metadata")

        if not client_id:
            client_id = self.config.oauth_client_id or f"cade-mcp-{self.config.name}"
        if client_secret is None:
            client_secret = self.config.oauth_client_secret

        data: dict[str, str] = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "http://127.0.0.1:9876/callback",
            "client_id": client_id,
            "code_verifier": code_verifier,
            "resource": self.config.url,
        }

        if client_secret:
            data["client_secret"] = client_secret

        resp = await client.post(
            token_endpoint,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if resp.status_code != 200:
            log.error(f"Token exchange failed ({resp.status_code}): {resp.text}")
            raise Exception(f"Token exchange failed ({resp.status_code}): {resp.text}")

        token_data = resp.json()
        expires_at = None
        if "expires_in" in token_data:
            expires_at = datetime.now() + timedelta(seconds=token_data["expires_in"])

        return MCPOAuthTokens(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "Bearer"),
            refresh_token=token_data.get("refresh_token"),
            expires_at=expires_at,
            scope=token_data.get("scope"),
        )

    async def refresh_tokens(
        self,
        auth_server_metadata: dict[str, Any],
        refresh_token: str,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> MCPOAuthTokens:
        """Refresh access token using refresh token."""
        client = await self._ensure_client()

        token_endpoint = auth_server_metadata.get("token_endpoint")
        if not token_endpoint:
            raise Exception("No token_endpoint in auth server metadata")

        if not client_id:
            client_id = self.config.oauth_client_id or f"cade-mcp-{self.config.name}"
        if client_secret is None:
            client_secret = self.config.oauth_client_secret

        data: dict[str, str] = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "resource": self.config.url,
        }

        if client_secret:
            data["client_secret"] = client_secret

        resp = await client.post(
            token_endpoint,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if resp.status_code != 200:
            raise Exception(f"Token refresh failed: {resp.text}")

        token_data = resp.json()
        expires_at = None
        if "expires_in" in token_data:
            expires_at = datetime.now() + timedelta(seconds=token_data["expires_in"])

        return MCPOAuthTokens(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "Bearer"),
            refresh_token=token_data.get("refresh_token", refresh_token),
            expires_at=expires_at,
            scope=token_data.get("scope"),
        )

    async def register_client(
        self,
        auth_server_metadata: dict[str, Any],
        client_name: str | None = None,
    ) -> tuple[str, str | None]:
        """Perform Dynamic Client Registration (RFC 7591)."""
        client = await self._ensure_client()

        registration_endpoint = auth_server_metadata.get("registration_endpoint")
        if not registration_endpoint:
            raise Exception(
                "Authorization server does not support Dynamic Client Registration. "
                "Please provide a client_id manually with --client-id."
            )

        client_metadata = {
            "client_name": client_name or f"cade-{self.config.name}",
            "redirect_uris": ["http://127.0.0.1:9876/callback"],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        }

        log.debug(f"Registering client at {registration_endpoint}")

        resp = await client.post(
            registration_endpoint,
            json=client_metadata,
            headers={"Content-Type": "application/json"},
        )

        if resp.status_code not in (200, 201):
            raise Exception(f"Client registration failed ({resp.status_code}): {resp.text}")

        registration_response = resp.json()
        client_id = registration_response.get("client_id")
        if not client_id:
            raise Exception("Registration response missing client_id")

        return client_id, registration_response.get("client_secret")

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class MCPToolManager(ToolManager):
    """Manages tools from MCP servers over HTTP or stdio transport."""

    def __init__(
        self,
        server_config: MCPServerConfig,
        server_store: MCPServerStore | None = None,
    ) -> None:
        self.config = server_config
        self._server_store = server_store
        self._tools_cache: list[dict[str, Any]] | None = None
        self._initialized = False

        # Transport-specific clients
        if server_config.transport == MCPTransportType.STDIO:
            self._stdio_connection = StdioMCPConnection(
                command=server_config.command or server_config.url,
                args=server_config.args,
                env=server_config.env,
            )
            self._client: httpx.AsyncClient | None = None
        else:
            self._stdio_connection: StdioMCPConnection | None = None
            self._client: httpx.AsyncClient | None = None

        self._session_id: str | None = None
        self._oauth_handler = MCPOAuthHandler(server_config)
        self._auth_server_metadata: dict[str, Any] | None = None

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers including authentication and session ID."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        if self.config.auth_type == MCPAuthType.BEARER and self.config.auth_value:
            headers["Authorization"] = f"Bearer {self.config.auth_value}"
        elif self.config.auth_type == MCPAuthType.API_KEY and self.config.auth_value:
            headers["X-API-Key"] = self.config.auth_value
        elif self.config.auth_type == MCPAuthType.OAUTH and self.config.oauth_tokens:
            token = self.config.oauth_tokens
            headers["Authorization"] = f"{token.token_type} {token.access_token}"

        return headers

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is created."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
            )
        return self._client

    async def _maybe_refresh_oauth_token(self) -> bool:
        """Refresh OAuth token if expired."""
        if self.config.auth_type != MCPAuthType.OAUTH:
            return False

        tokens = self.config.oauth_tokens
        if not tokens or not tokens.is_expired():
            return False

        if not tokens.refresh_token:
            return False

        if not self._auth_server_metadata:
            rs_meta = await self._oauth_handler.fetch_protected_resource_metadata()
            if rs_meta:
                auth_servers = rs_meta.get("authorization_servers", [])
                if auth_servers:
                    self._auth_server_metadata = (
                        await self._oauth_handler.fetch_authorization_server_metadata(
                            auth_servers[0]
                        )
                    )

        if not self._auth_server_metadata:
            return False

        try:
            new_tokens = await self._oauth_handler.refresh_tokens(
                self._auth_server_metadata,
                tokens.refresh_token,
                self.config.oauth_client_id,
                self.config.oauth_client_secret,
            )
            self.config.oauth_tokens = new_tokens

            if self._server_store:
                self._server_store.add(self.config)

            log.info(f"Refreshed OAuth token for MCP server '{self.config.name}'")
            return True
        except Exception as e:
            log.warning(f"Failed to refresh OAuth token: {e}")
            return False

    async def _handle_401_response(self, response: httpx.Response) -> str | None:
        """Handle 401 response per MCP OAuth spec."""
        metadata_url, scope = await self._oauth_handler.discover_from_401(response)

        rs_metadata = await self._oauth_handler.fetch_protected_resource_metadata(metadata_url)
        if not rs_metadata:
            return None

        auth_servers = rs_metadata.get("authorization_servers", [])
        if not auth_servers:
            return None

        as_metadata = await self._oauth_handler.fetch_authorization_server_metadata(auth_servers[0])
        if not as_metadata:
            return None

        self._auth_server_metadata = as_metadata
        self.config.oauth_authorization_server = auth_servers[0]

        auth_url, code_verifier, state = await self._oauth_handler.start_oauth_flow(
            as_metadata, scope, self.config.oauth_client_id
        )

        self._pending_code_verifier = code_verifier
        self._pending_state = state

        return auth_url

    async def _send_notification(self, method: str) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        if self.config.transport == MCPTransportType.STDIO:
            # Send notification via stdio (no response expected)
            if not self._stdio_connection:
                return

            await self._stdio_connection.start()

            payload: dict[str, Any] = {
                "jsonrpc": "2.0",
                "method": method,
            }

            try:
                # Send notification but don't wait for response (notifications don't have IDs)
                if self._stdio_connection.process and self._stdio_connection.process.stdin:
                    line = json.dumps(payload) + "\n"
                    self._stdio_connection.process.stdin.write(line.encode())
                    await self._stdio_connection.process.stdin.drain()
            except Exception as e:
                log.warning(f"Stdio notification '{method}' failed: {e}")
            return

        client = await self._ensure_client()

        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
        }

        headers = self._get_headers()
        try:
            response = await client.post(self.config.url, json=payload, headers=headers)
            if response.status_code not in (200, 202, 204):
                log.warning(
                    f"MCP notification '{method}' got unexpected status: {response.status_code}"
                )
        except Exception as e:
            log.warning(f"MCP notification '{method}' failed: {e}")

    async def _send_request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        """Send a JSON-RPC request to the MCP server."""
        # Route to appropriate transport
        if self.config.transport == MCPTransportType.STDIO:
            return await self._send_stdio_request(method, params)
        else:
            return await self._send_http_request(method, params)

    async def _send_stdio_request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        """Send a JSON-RPC request via stdio transport."""
        if not self._stdio_connection:
            raise Exception("Stdio connection not initialized")

        # Ensure subprocess is started
        await self._stdio_connection.start()

        request_id = str(uuid.uuid4())
        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params:
            payload["params"] = params

        try:
            response = await self._stdio_connection.send_request(payload)

            if "error" in response:
                raise Exception(f"MCP error: {response['error'].get('message', 'Unknown error')}")

            return response.get("result")

        except Exception as e:
            log.error(f"MCP stdio request failed for {self.config.name}: {e}")
            raise

    async def _send_http_request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        """Send a JSON-RPC request via HTTP transport."""
        await self._maybe_refresh_oauth_token()

        client = await self._ensure_client()

        request_id = str(uuid.uuid4())
        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params:
            payload["params"] = params

        try:
            headers = self._get_headers()
            response = await client.post(self.config.url, json=payload, headers=headers)

            if "mcp-session-id" in response.headers:
                self._session_id = response.headers["mcp-session-id"]
                log.debug(
                    f"Captured MCP session ID for '{self.config.name}': {self._session_id[:8]}..."
                )

            if response.status_code == 401:
                auth_url = await self._handle_401_response(response)
                raise ToolAuthorizationRequired(
                    f"MCP:{self.config.name}",
                    authorization_url=auth_url,
                )

            if response.status_code == 403:
                www_auth = response.headers.get("WWW-Authenticate", "")
                auth_params = self._oauth_handler.parse_www_authenticate(www_auth)
                if auth_params.get("error") == "insufficient_scope":
                    raise ToolAuthorizationRequired(
                        f"MCP:{self.config.name}",
                        authorization_url=None,
                    )

            response.raise_for_status()

            content_type = response.headers.get("content-type", "")

            if "text/event-stream" in content_type:
                return await self._parse_sse_response(response, request_id)
            else:
                result = response.json()
                if "error" in result:
                    raise Exception(f"MCP error: {result['error'].get('message', 'Unknown error')}")
                return result.get("result")

        except httpx.HTTPStatusError as e:
            raise Exception(f"MCP HTTP error: {e}")
        except ToolAuthorizationRequired:
            raise
        except Exception as e:
            log.error(f"MCP request failed for {self.config.name}: {e}")
            raise

    async def _parse_sse_response(self, response: httpx.Response, request_id: str) -> Any:
        """Parse Server-Sent Events response."""
        result = None
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]
                if data.strip():
                    try:
                        event = json.loads(data)
                        if event.get("id") == request_id:
                            if "error" in event:
                                raise Exception(f"MCP error: {event['error'].get('message')}")
                            result = event.get("result")
                    except json.JSONDecodeError:
                        continue
        return result

    async def initialize(self) -> bool:
        """Initialize connection to MCP server."""
        if self._initialized:
            return True

        try:
            result = await self._send_request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "cade", "version": "1.0.0"},
                },
            )

            if result:
                self._initialized = True
                await self._send_notification("notifications/initialized")
                log.info(f"MCP server '{self.config.name}' initialized")
                return True

            return False

        except Exception as e:
            log.error(f"Failed to initialize MCP server '{self.config.name}': {e}")
            return False

    async def get_tools(self) -> list[dict[str, Any]]:
        """Get available tools from the MCP server."""
        if self._tools_cache is not None:
            return self._tools_cache

        if not self._initialized:
            success = await self.initialize()
            if not success:
                return []

        try:
            result = await self._send_request("tools/list")

            if not result or "tools" not in result:
                return []

            self._tools_cache = []
            for mcp_tool in result["tools"]:
                openai_tool = self._convert_mcp_to_openai(mcp_tool)
                self._tools_cache.append(openai_tool)

            log.info(f"Loaded {len(self._tools_cache)} tools from MCP server '{self.config.name}'")
            return self._tools_cache

        except Exception as e:
            log.error(f"Failed to list tools from MCP '{self.config.name}': {e}")
            return []

    def _sanitize_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Sanitize JSON schema to be valid for OpenAI."""
        if not isinstance(schema, dict):
            return schema

        result = schema.copy()

        if result.get("type") == "object" and "properties" not in result:
            result["properties"] = {}

        if "properties" in result and isinstance(result["properties"], dict):
            result["properties"] = {
                k: self._sanitize_schema(v) for k, v in result["properties"].items()
            }

        if "items" in result and isinstance(result["items"], dict):
            result["items"] = self._sanitize_schema(result["items"])

        for key in ("anyOf", "oneOf", "allOf"):
            if key in result and isinstance(result[key], list):
                result[key] = [self._sanitize_schema(item) for item in result[key]]

        return result

    def _convert_mcp_to_openai(self, mcp_tool: dict[str, Any]) -> dict[str, Any]:
        """Convert MCP tool schema to OpenAI function schema."""
        input_schema = mcp_tool.get("inputSchema", {"type": "object", "properties": {}})
        sanitized_schema = self._sanitize_schema(input_schema)

        return {
            "type": "function",
            "function": {
                "name": mcp_tool["name"],
                "description": mcp_tool.get("description", ""),
                "parameters": sanitized_schema,
            },
        }

    def _extract_text_from_content(self, content: list[dict[str, Any]]) -> str | None:
        """Extract text from MCP content array."""
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                return item.get("text")
        return None

    def _parse_arcade_error(self, error_text: str) -> str:
        """Parse arcade-mcp-server error object string to extract clean error message."""
        import re

        # Try to extract message field: message="..."
        message_match = re.search(r'message="([^"]*)"', error_text)
        if message_match:
            error_msg = message_match.group(1)
            # Remove error prefixes like "[TOOL_RUNTIME_FATAL] ToolExecutionError during execution of tool 'X':"
            error_msg = re.sub(r"^\[.*?\]\s*\w+Error.*?:\s*", "", error_msg)
            # Keep only the actual error after the last colon
            if ":" in error_msg:
                error_msg = error_msg.split(":")[-1].strip()
        else:
            # If we can't parse the error, show a preview of the raw error
            error_preview = error_text[:200] if len(error_text) > 200 else error_text
            error_msg = f"Tool execution failed: {error_preview}"

        # Check for TypeError in stacktrace
        type_error_match = re.search(r"TypeError:\s*(.+?)(?:\\n|$)", error_text)
        if type_error_match:
            error_msg = f"Missing required parameter: {type_error_match.group(1).strip()}"

        return error_msg

    async def execute(self, name: str, inputs: dict[str, Any]) -> Any:
        """Execute a tool on the MCP server."""
        if not self._initialized:
            success = await self.initialize()
            if not success:
                raise Exception(f"MCP server '{self.config.name}' not initialized")

        try:
            result = await self._send_request(
                "tools/call",
                {"name": name, "arguments": inputs},
            )

            # Check if result is an error from arcade-mcp-server
            if isinstance(result, dict) and result.get("isError"):
                error_content = result.get("content", [])
                error_text = self._extract_text_from_content(error_content)

                if error_text:
                    error_msg = self._parse_arcade_error(error_text)
                    log.debug(f"Parsed arcade error for {name}: {error_msg[:100]}")
                    raise Exception(error_msg)

                # Fallback if we can't extract text from error content
                log.warning(
                    f"Could not extract error text from {name}, content: {str(error_content)[:200]}"
                )
                raise Exception(f"Tool execution failed: {error_content}")

            # Check for successful result with content
            if isinstance(result, dict) and "content" in result:
                content_items = result["content"]
                text_parts = []
                for item in content_items:
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                return "\n".join(text_parts) if text_parts else result

            return result

        except Exception as e:
            log.error(f"MCP tool execution failed for '{name}': {e}")
            raise Exception(f"Failed to execute MCP tool '{name}': {e}")

    async def check_status(self) -> tuple[bool, str]:
        """Check if MCP server is reachable and initialize the session."""
        try:
            self._initialized = False
            self._session_id = None

            success = await self.initialize()
            if success:
                return True, "Connected"
            else:
                return False, "Initialization failed"

        except httpx.ConnectError:
            return False, "Connection failed"
        except ToolAuthorizationRequired:
            return False, "Authentication required"
        except Exception as e:
            return False, str(e)[:50]

    async def complete_oauth_flow(self, authorization_code: str) -> bool:
        """Complete OAuth flow by exchanging authorization code for tokens."""
        if not self._auth_server_metadata:
            log.error("No auth server metadata - cannot complete OAuth flow")
            return False

        if not hasattr(self, "_pending_code_verifier"):
            log.error("No pending PKCE verifier - OAuth flow not started")
            return False

        try:
            tokens = await self._oauth_handler.exchange_code_for_tokens(
                self._auth_server_metadata,
                authorization_code,
                self._pending_code_verifier,
                self.config.oauth_client_id,
                self.config.oauth_client_secret,
            )

            self.config.auth_type = MCPAuthType.OAUTH
            self.config.oauth_tokens = tokens

            if self._server_store:
                self._server_store.add(self.config)

            del self._pending_code_verifier
            if hasattr(self, "_pending_state"):
                del self._pending_state

            if self._client:
                await self._client.aclose()
                self._client = None

            log.info(f"OAuth flow completed for MCP server '{self.config.name}'")
            return True

        except Exception as e:
            log.error(f"Failed to complete OAuth flow: {e}")
            return False

    async def close(self) -> None:
        """Close connections and reset session state."""
        if self._stdio_connection:
            await self._stdio_connection.close()
        if self._client:
            await self._client.aclose()
            self._client = None
        self._session_id = None
        self._initialized = False
        await self._oauth_handler.close()
