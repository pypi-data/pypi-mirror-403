# MCP Sora

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for AI video generation using [Sora](https://openai.com/sora) through the [AceDataCloud API](https://platform.acedata.cloud).

Generate AI videos directly from Claude, VS Code, or any MCP-compatible client.

## Features

- **Text-to-Video** - Generate videos from text descriptions
- **Image-to-Video** - Animate images and create videos from reference images
- **Character Videos** - Reuse characters across different scenes
- **Async Generation** - Webhook callbacks for production workflows
- **Multiple Orientations** - Landscape, portrait, and square videos
- **Task Tracking** - Monitor generation progress and retrieve results

## Quick Start

### 1. Get API Token

Get your API token from [AceDataCloud Platform](https://platform.acedata.cloud):

1. Sign up or log in
2. Navigate to [Sora Videos API](https://platform.acedata.cloud/documents/99a24421-2e22-4028-8201-e19cb834b67e)
3. Click "Acquire" to get your token

### 2. Install

```bash
# Clone the repository
git clone https://github.com/AceDataCloud/mcp-sora.git
cd mcp-sora

# Install with pip
pip install -e .

# Or with uv (recommended)
uv pip install -e .
```

### 3. Configure

```bash
# Copy example environment file
cp .env.example .env

# Edit with your API token
echo "ACEDATACLOUD_API_TOKEN=your_token_here" > .env
```

### 4. Run

```bash
# Run the server
mcp-sora

# Or with Python directly
python main.py
```

## Claude Desktop Integration

Add to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "sora": {
      "command": "mcp-sora",
      "env": {
        "ACEDATACLOUD_API_TOKEN": "your_api_token_here"
      }
    }
  }
}
```

Or if using uv:

```json
{
  "mcpServers": {
    "sora": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-sora", "mcp-sora"],
      "env": {
        "ACEDATACLOUD_API_TOKEN": "your_api_token_here"
      }
    }
  }
}
```

## Available Tools

### Video Generation

| Tool | Description |
|------|-------------|
| `sora_generate_video` | Generate video from a text prompt |
| `sora_generate_video_from_image` | Generate video from reference images |
| `sora_generate_video_with_character` | Generate video with a character from reference video |
| `sora_generate_video_async` | Generate video with callback notification |

### Tasks

| Tool | Description |
|------|-------------|
| `sora_get_task` | Query a single task status |
| `sora_get_tasks_batch` | Query multiple tasks at once |

### Information

| Tool | Description |
|------|-------------|
| `sora_list_models` | List available Sora models |
| `sora_list_actions` | List available API actions |

## Usage Examples

### Generate Video from Prompt

```
User: Create a video of a sunset over mountains

Claude: I'll generate a sunset video for you.
[Calls sora_generate_video with prompt="A beautiful sunset over mountains..."]
```

### Generate from Image

```
User: Animate this image of a city skyline

Claude: I'll bring this image to life.
[Calls sora_generate_video_from_image with image_urls and prompt]
```

### Character-based Video

```
User: Use the robot character in a new scene

Claude: I'll create a new scene with the robot character.
[Calls sora_generate_video_with_character with character_url and prompt]
```

## Available Models

| Model | Max Duration | Quality | Features |
|-------|--------------|---------|----------|
| `sora-2` | 15 seconds | Good | Standard generation |
| `sora-2-pro` | 25 seconds | Best | Higher quality, longer videos |

### Video Options

**Size:**
- `small` - Lower resolution, faster generation
- `large` - Higher resolution (recommended)

**Orientation:**
- `landscape` - 16:9 (YouTube, presentations)
- `portrait` - 9:16 (TikTok, Instagram Stories)
- `square` - 1:1 (Instagram posts)

**Duration:**
- `10` seconds - All models
- `15` seconds - All models
- `25` seconds - sora-2-pro only

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ACEDATACLOUD_API_TOKEN` | API token from AceDataCloud | **Required** |
| `ACEDATACLOUD_API_BASE_URL` | API base URL | `https://api.acedata.cloud` |
| `SORA_DEFAULT_MODEL` | Default model | `sora-2` |
| `SORA_DEFAULT_SIZE` | Default video size | `large` |
| `SORA_DEFAULT_DURATION` | Default duration (seconds) | `15` |
| `SORA_DEFAULT_ORIENTATION` | Default orientation | `landscape` |
| `SORA_REQUEST_TIMEOUT` | Request timeout (seconds) | `300` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Command Line Options

```bash
mcp-sora --help

Options:
  --version          Show version
  --transport        Transport mode: stdio (default) or http
  --port             Port for HTTP transport (default: 8000)
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/AceDataCloud/mcp-sora.git
cd mcp-sora

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install with dev dependencies
pip install -e ".[dev,test]"
```

### Run Tests

```bash
# Run unit tests
pytest

# Run with coverage
pytest --cov=core --cov=tools

# Run integration tests (requires API token)
pytest tests/test_integration.py -m integration
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type check
mypy core tools
```

### Build & Publish

```bash
# Install build dependencies
pip install -e ".[release]"

# Build package
python -m build

# Upload to PyPI
twine upload dist/*
```

## Project Structure

```
MCPSora/
├── core/                   # Core modules
│   ├── __init__.py
│   ├── client.py          # HTTP client for Sora API
│   ├── config.py          # Configuration management
│   ├── exceptions.py      # Custom exceptions
│   ├── server.py          # MCP server initialization
│   ├── types.py           # Type definitions
│   └── utils.py           # Utility functions
├── tools/                  # MCP tool definitions
│   ├── __init__.py
│   ├── video_tools.py     # Video generation tools
│   ├── task_tools.py      # Task query tools
│   └── info_tools.py      # Information tools
├── prompts/                # MCP prompt templates
│   └── __init__.py
├── tests/                  # Test suite
│   ├── conftest.py
│   ├── test_client.py
│   ├── test_config.py
│   ├── test_integration.py
│   └── test_utils.py
├── .env.example           # Environment template
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── main.py                # Entry point
├── pyproject.toml         # Project configuration
└── README.md
```

## API Reference

This server wraps the [AceDataCloud Sora API](https://platform.acedata.cloud/documents/99a24421-2e22-4028-8201-e19cb834b67e):

- [Sora Videos API](https://platform.acedata.cloud/documents/99a24421-2e22-4028-8201-e19cb834b67e) - Video generation
- [Sora Tasks API](https://platform.acedata.cloud/documents/c9d81bad-9064-4796-86b6-4fb43cc93a16) - Task queries

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [AceDataCloud Platform](https://platform.acedata.cloud)
- [Sora Official](https://openai.com/sora)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

---

Made with love by [AceDataCloud](https://platform.acedata.cloud)
