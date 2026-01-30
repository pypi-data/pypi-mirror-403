"""
OAuth authentication module for CadeCoder CLI.

Uses arcade-core for OAuth 2.0 Authorization Code flow with PKCE.
Credentials are shared with arcade-cli at ~/.arcade/credentials.yaml.
"""

import secrets
import threading
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from arcade_core.auth_tokens import (
    CLIConfig,
    TokenResponse,
    fetch_cli_config,
    get_valid_access_token,
)
from arcade_core.config_model import Config
from authlib.integrations.httpx_client import OAuth2Client
from rich.console import Console

from cadecoder.core.constants import load_template

console = Console()

# OAuth constants
DEFAULT_SCOPES = "openid offline_access"
LOCAL_CALLBACK_PORT = 9905


class WhoAmIResponse:
    """Response from Coordinator /whoami endpoint."""

    def __init__(
        self,
        account_id: str,
        email: str,
        organizations: list[dict[str, Any]] | None = None,
        projects: list[dict[str, Any]] | None = None,
    ) -> None:
        self.account_id = account_id
        self.email = email
        self.organizations = organizations or []
        self.projects = projects or []

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WhoAmIResponse":
        """Create from API response dict."""
        return cls(
            account_id=data.get("account_id", ""),
            email=data.get("email", ""),
            organizations=data.get("organizations", []),
            projects=data.get("projects", []),
        )

    def get_selected_org(self) -> dict[str, Any] | None:
        """Get the default org or first available."""
        if not self.organizations:
            return None
        for org in self.organizations:
            if org.get("is_default"):
                return org
        return self.organizations[0]

    def get_selected_project(self) -> dict[str, Any] | None:
        """Get the default project or first available."""
        if not self.projects:
            return None
        for proj in self.projects:
            if proj.get("is_default"):
                return proj
        return self.projects[0]


def create_oauth_client(cli_config: CLIConfig) -> OAuth2Client:
    """Create an authlib OAuth2Client configured for the CLI."""
    return OAuth2Client(
        client_id=cli_config.client_id,
        token_endpoint=cli_config.token_endpoint,
        code_challenge_method="S256",
    )


def generate_authorization_url(
    client: OAuth2Client,
    cli_config: CLIConfig,
    redirect_uri: str,
    state: str,
) -> tuple[str, str]:
    """Generate OAuth authorization URL with PKCE."""
    code_verifier = secrets.token_urlsafe(64)
    url, _ = client.create_authorization_url(
        cli_config.authorization_endpoint,
        redirect_uri=redirect_uri,
        scope=DEFAULT_SCOPES,
        state=state,
        code_verifier=code_verifier,
    )
    return url, code_verifier


def exchange_code_for_tokens(
    client: OAuth2Client,
    code: str,
    redirect_uri: str,
    code_verifier: str,
) -> TokenResponse:
    """Exchange authorization code for tokens using authlib."""
    token = client.fetch_token(
        client.session.metadata["token_endpoint"],
        grant_type="authorization_code",
        code=code,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier,
    )
    return TokenResponse(
        access_token=token["access_token"],
        refresh_token=token["refresh_token"],
        expires_in=token["expires_in"],
        token_type=token["token_type"],
    )


def fetch_whoami(coordinator_url: str, access_token: str) -> WhoAmIResponse:
    """Fetch user info from the Coordinator."""
    import httpx

    url = f"{coordinator_url}/api/v1/auth/whoami"
    response = httpx.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json().get("data", {})
    return WhoAmIResponse.from_dict(data)


def save_credentials_from_whoami(
    tokens: TokenResponse,
    whoami: WhoAmIResponse,
    coordinator_url: str,
) -> None:
    """Save OAuth credentials using arcade-core Config model."""
    from datetime import datetime, timedelta

    from arcade_core.config_model import AuthConfig, ContextConfig, UserConfig

    expires_at = datetime.now() + timedelta(seconds=tokens.expires_in)

    context = None
    selected_org = whoami.get_selected_org()
    selected_project = whoami.get_selected_project()

    if selected_org and selected_project:
        org_id = selected_org.get("org_id") or selected_org.get("organization_id", "")
        context = ContextConfig(
            org_id=org_id,
            org_name=selected_org.get("name", ""),
            project_id=selected_project.get("project_id", ""),
            project_name=selected_project.get("name", ""),
        )

    config = Config(
        coordinator_url=coordinator_url,
        auth=AuthConfig(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_at=expires_at,
        ),
        user=UserConfig(email=whoami.email),
        context=context,
    )
    config.save_to_file()


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback."""

    def __init__(
        self,
        *args: Any,
        state: str,
        result_holder: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        self.state = state
        self.result_holder = result_holder
        super().__init__(*args, **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress logging to stdout."""
        pass

    def do_GET(self) -> None:
        """Handle GET request (OAuth callback)."""
        query_string = self.path.split("?", 1)[-1] if "?" in self.path else ""
        params = parse_qs(query_string)

        returned_state = params.get("state", [None])[0]
        code = params.get("code", [None])[0]
        error = params.get("error", [None])[0]
        error_description = params.get("error_description", [None])[0]

        if returned_state != self.state:
            self.result_holder["error"] = "Invalid state parameter. Possible CSRF attack."
            self._send_error_response()
            return

        if error:
            self.result_holder["error"] = error_description or error
            self._send_error_response()
            return

        if not code:
            self.result_holder["error"] = "No authorization code received."
            self._send_error_response()
            return

        self.result_holder["code"] = code
        self._send_success_response()

    def _send_success_response(self) -> None:
        """Send success HTML response."""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(load_template("login_success.html"))
        threading.Thread(target=self.server.shutdown).start()

    def _send_error_response(self) -> None:
        """Send error HTML response."""
        self.send_response(400)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(load_template("login_failed.html"))
        threading.Thread(target=self.server.shutdown).start()


class OAuthCallbackServer:
    """Local HTTP server for OAuth callback."""

    def __init__(self, state: str, port: int = LOCAL_CALLBACK_PORT) -> None:
        self.state = state
        self.port = port
        self.httpd: HTTPServer | None = None
        self.result: dict[str, Any] = {}

    def _make_handler(self) -> type[OAuthCallbackHandler]:
        """Create handler factory with state and result holder."""
        state = self.state
        result = self.result

        class HandlerWithState(OAuthCallbackHandler):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(*args, state=state, result_holder=result, **kwargs)

        return HandlerWithState

    def run_server(self) -> None:
        """Start the callback server."""
        server_address = ("", self.port)
        self.httpd = HTTPServer(server_address, self._make_handler())
        self.httpd.serve_forever()

    def start(self) -> int | None:
        """Start the HTTP server in the background.

        Returns the actual bound port or None on failure.
        """
        try:
            if self.port == 0:
                temp = HTTPServer(("", 0), self._make_handler())
                self.port = temp.server_port
                temp.server_close()

            self._server_thread = threading.Thread(target=self.run_server, daemon=True)
            self._server_thread.start()
            return self.port
        except Exception:
            return None

    def wait_for_callback(self, timeout: float | None = None) -> bool:
        """Wait for callback thread to complete."""
        if hasattr(self, "_server_thread"):
            self._server_thread.join(timeout=timeout)
            return "code" in self.result
        return False

    def shutdown_server(self) -> None:
        """Shut down the callback server."""
        if self.httpd:
            self.httpd.shutdown()

    def get_redirect_uri(self) -> str:
        """Get the redirect URI for this server."""
        return f"http://localhost:{self.port}/callback"


class OAuthLoginError(Exception):
    """Error during OAuth login flow."""

    pass


def build_coordinator_url(host: str, port: int | None = None) -> str:
    """Build the Coordinator URL from host and optional port."""
    if port:
        scheme = "http" if host == "localhost" else "https"
        return f"{scheme}://{host}:{port}"
    scheme = "http" if host == "localhost" else "https"
    default_port = ":8000" if host == "localhost" else ""
    return f"{scheme}://{host}{default_port}"


def perform_oauth_login(
    coordinator_url: str,
    on_status: Any | None = None,
) -> tuple[TokenResponse, WhoAmIResponse]:
    """Perform the complete OAuth login flow.

    Args:
        coordinator_url: Base URL of the Coordinator
        on_status: Optional callback for status messages

    Returns:
        Tuple of (TokenResponse, WhoAmIResponse)

    Raises:
        OAuthLoginError: If any step of the login flow fails
    """

    def status(msg: str) -> None:
        if on_status:
            on_status(msg)

    # Step 1: Fetch OAuth config from Coordinator
    try:
        cli_config = fetch_cli_config(coordinator_url)
    except Exception as e:
        raise OAuthLoginError(f"Could not connect to Arcade at {coordinator_url}") from e

    # Step 2: Create OAuth client and prepare PKCE
    oauth_client = create_oauth_client(cli_config)
    state = str(uuid.uuid4())

    # Step 3: Start local callback server
    server = OAuthCallbackServer(state)
    local_port = server.start()
    if local_port is None:
        raise OAuthLoginError("Failed to start callback server.")

    redirect_uri = server.get_redirect_uri()

    # Step 4: Generate authorization URL and open browser
    auth_url, code_verifier = generate_authorization_url(
        oauth_client, cli_config, redirect_uri, state
    )

    status(f"Opening browser to: {auth_url}")
    if not webbrowser.open(auth_url):
        status(f"Copy this URL into your browser:\n{auth_url}")

    # Step 5: Wait for callback
    server.wait_for_callback(timeout=300)

    # Check for errors from callback
    if "error" in server.result:
        raise OAuthLoginError(f"Login failed: {server.result['error']}")

    if "code" not in server.result:
        raise OAuthLoginError("No authorization code received (timed out).")

    # Step 6: Exchange code for tokens
    code = server.result["code"]
    tokens = exchange_code_for_tokens(oauth_client, code, redirect_uri, code_verifier)

    # Step 7: Fetch user info
    whoami = fetch_whoami(coordinator_url, tokens.access_token)

    # Validate org/project exist
    if not whoami.get_selected_org():
        raise OAuthLoginError(
            "No organizations found for your account. "
            "Please contact support@arcade.dev for assistance."
        )

    if not whoami.get_selected_project():
        org = whoami.get_selected_org()
        org_name = org.get("name", "unknown") if org else "unknown"
        raise OAuthLoginError(
            f"No projects found in organization '{org_name}'. "
            "Please contact support@arcade.dev for assistance."
        )

    return tokens, whoami


def check_existing_login(suppress_message: bool = False) -> bool:
    """Check if the user is already logged in.

    Args:
        suppress_message: If True, suppress the logged in message.

    Returns:
        True if the user is already logged in, False otherwise.
    """
    try:
        config = Config.load_from_file()
        if config.is_authenticated() and config.auth:
            email = config.user.email if config.user else "unknown"
            context = config.context
            if context:
                org_name = context.org_name
                project_name = context.project_name
            else:
                org_name = "unknown"
                project_name = "unknown"

            if not suppress_message:
                console.print(
                    f"You're already logged in as {email}.",
                    style="bold green",
                )
                console.print(f"Active: {org_name} / {project_name}", style="dim")
            return True
    except FileNotFoundError:
        pass
    except ValueError as e:
        console.print(f"Error reading config: {e}", style="bold red")

    return False


def get_access_token(coordinator_url: str | None = None) -> str:
    """Get a valid access token, refreshing if necessary.

    This is the main function to use when making authenticated API calls.

    Args:
        coordinator_url: Optional coordinator URL override

    Returns:
        Valid access token

    Raises:
        ValueError: If not logged in or token refresh fails
    """
    return get_valid_access_token(coordinator_url)


# For backward compatibility with legacy API key format
def _check_legacy_credentials() -> tuple[str, str] | None:
    """Check for legacy API key credentials.

    Returns:
        Tuple of (api_key, email) if found, None otherwise.
    """
    import yaml

    creds_path = Path.home() / ".arcade" / "credentials.yaml"
    if not creds_path.exists():
        return None

    try:
        with creds_path.open() as f:
            data = yaml.safe_load(f) or {}

        cloud = data.get("cloud", {})
        if isinstance(cloud, dict) and "api" in cloud:
            api_key = cloud.get("api", {}).get("key")
            email = cloud.get("user", {}).get("email")
            if api_key and email:
                return api_key, email
    except Exception:
        pass

    return None
