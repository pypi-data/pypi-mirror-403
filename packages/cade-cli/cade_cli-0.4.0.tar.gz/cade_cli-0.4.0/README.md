# Cade

An AI-powered CLI agent for coding and everyday tasks. Powered by [Arcade.dev](https://arcade.dev).

## Installation

### Prerequisites

- Python 3.11+
- Arcade account ([arcade.dev](https://arcade.dev))
- AI provider API key: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

### Homebrew (macOS/Linux)

```bash
brew tap ArcadeAI/tap
brew install cade
```

### Install with uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install cade-cli
```

### Install with pip

```bash
pip install cade-cli
```

### From Source

```bash
git clone https://github.com/arcadeai-labs/cade.git
cd cade
uv venv --python 3.11
source .venv/bin/activate
uv sync
```

### Authenticate

```bash
cade login
```

## Usage

### Start a Chat

```bash
cade
```

### Resume a Thread

```bash
cade -r                        # Resume most recent
cade resume "my-project"       # Resume by name
```

### Authentication

Cade uses Arcade Cloud for authentication and shares credentials with arcade-cli.

```bash
cade login                      # Log in to Arcade Cloud
cade logout                     # Log out
cade whoami                     # Show current login status
```

### Context Management

Switch between organizations and projects for Arcade Cloud features.

```bash
cade context show               # Show current org/project
cade context list               # List available orgs and projects
cade context switch -i          # Interactive selection
cade context switch --org my-org --project my-project
```

### Single Message Mode

```bash
cade -m "What files are in this directory?"
cat error.log | cade -m "What went wrong?"
```

### Options

| Option | Description |
|--------|-------------|
| `-r`, `--resume` | Resume the most recent thread |
| `-m`, `--message` | Single message mode (non-interactive) |
| `-L`, `--local-only` | Disable remote tools (use only local tools) |
| `-v`, `--verbose` | Enable debug logging |
| `--version` | Show version |

### In-Chat Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/logs` | View recent log entries |
| `/clear` | Clear the screen |
| `/copy` | Copy last response to clipboard |
| `Ctrl+C` | Exit |

## Thread Management

```bash
cade thread list                          # List all threads
cade thread list --branch main            # Filter by branch
cade thread get <thread-id>               # Get thread details
cade thread get <thread-id> --messages    # Show messages
cade thread delete <thread-id>            # Delete thread
```

## Tool Management

Tools come from three sources: local, Arcade Cloud, and MCP servers.

```bash
cade tool list                    # List all tools
cade tool list --source local     # Filter by source
cade tool search "file"           # Search tools
cade tool info Local_ReadFile     # Tool details
```

### Built-in Tools

| Tool | Description |
|------|-------------|
| `Local_ReadFile` | Read file contents |
| `Local_WriteFile` | Write or append to files |
| `Local_ListFiles` | List directory contents |
| `Local_SearchText` | Search for text patterns |
| `Local_ExecuteShell` | Run shell commands |
| `Local_CreateDirectory` | Create directories |
| `Local_DeleteFile` | Delete files |
| `Local_GetGitStatus` | Get git status |

## MCP Servers

Connect to [MCP](https://modelcontextprotocol.io/) servers for extended capabilities.

```bash
cade mcp list                                                    # List servers
cade mcp add my-server http://localhost:8080                     # Add server
cade mcp add my-server http://localhost:8080 --auth bearer -t <token>  # With auth
cade mcp test my-server                                          # Test connection
cade mcp enable my-server                                        # Enable
cade mcp disable my-server                                       # Disable
cade mcp rm my-server                                            # Remove
```

## Configuration

Config is stored in `~/.cadecoder/`:

| File | Description |
|------|-------------|
| `cadecoder.toml` | Settings |
| `cadecoder_history.db` | Thread history |
| `cadecoder.log` | Logs |
| `mcp_servers.yaml` | MCP server configs |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENAI_BASE_URL` | Custom OpenAI-compatible API endpoint |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `ARCADE_API_KEY` | Arcade API key (alternative to OAuth) |
| `ARCADE_BASE_URL` | Custom Arcade API endpoint |
| `CADE_LOCAL_ONLY` | Set to `1` to disable remote tools |
| `CADECODER_HOME` | Override config directory |

### Example Config

```toml
# ~/.cadecoder/cadecoder.toml

default_model = "gpt-4.1"
debug_mode = false
use_responses_api = true

[responses_config]
enabled = true
streaming_enabled = true

[model_settings]
provider = "openai"
model = "gpt-4.1"

[tool_settings]
# Tool filtering is managed via MCP server configuration
# See: cade mcp add --help
```

## Using Local or Custom LLMs

Cade works with any OpenAI-compatible API, including local servers (Ollama, vLLM, llama.cpp) and alternative cloud providers (Together AI, Groq, Fireworks).

### Local-Only Mode

When using local LLMs, you can skip Arcade Cloud authentication entirely with `--local-only`:

```bash
# Local Ollama server without Arcade Cloud
cade chat --local-only --endpoint "http://localhost:11434/v1" --model "llama3"

# Or via environment variable
CADE_LOCAL_ONLY=1 cade chat --endpoint "http://localhost:11434/v1" --model "llama3"
```

This disables remote tools and uses only local tools. Cade will also gracefully fall back to local-only mode if Arcade Cloud authentication is not configured.

### Via CLI Flags

```bash
# Local Ollama server
cade chat --endpoint "http://localhost:11434/v1" --model "glm-4.7-flash:latest"

# vLLM server
cade chat -e http://localhost:8000/v1 -m mistral-7b
```

### Via Environment Variables

```bash
export OPENAI_BASE_URL="http://localhost:11434/v1"
export OPENAI_API_KEY="ollama"  # Dummy key for local model
cade chat --model glm-4.7-flash:latest
```

### Via Config File

```toml
# ~/.cadecoder/cadecoder.toml

default_model = "glm-4.7-flash:latest"

[model_settings]
host = "http://localhost:11434/v1"
api_key = "ollama"
```

After configuring the TOML file:

```bash
cade chat
```

### `cade chat` Configuration Precedence

Settings are resolved in this order (first is used):

1. CLI flags (`--endpoint`, `--model`)
2. Environment variables (`OPENAI_BASE_URL`, `OPENAI_API_KEY`)
3. Config file (`model_settings.host`, `model_settings.api_key`)
4. Hardcoded defaults

## Contributing

### Development Setup

```bash
git clone https://github.com/arcadeai-labs/cade.git
cd cade
uv sync --extra dev
```

### Run Tests

```bash
pytest
ruff check src/
ruff format src/
```

### Code Style

- Python 3.11+ with modern type hints (`dict`, `list`, `| None`)
- Ruff for linting and formatting
- Pytest for testing
- Docstrings for public functions and classes

### Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run `ruff check . && pytest`
5. Open a Pull Request

## Resources

- [arcade.dev](https://arcade.dev)
- [Documentation](https://docs.arcade.dev)
- [Issues](https://github.com/arcadeai-labs/cade/issues)
- [Releases](https://github.com/arcadeai-labs/cade/releases)

## License

MIT
