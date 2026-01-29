# MCP Luma

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for AI video generation using [Luma Dream Machine](https://lumalabs.ai/dream-machine) through the [AceDataCloud API](https://platform.acedata.cloud).

Generate AI videos directly from Claude, VS Code, or any MCP-compatible client.

## Features

- **Text to Video** - Create AI-generated videos from text prompts
- **Image to Video** - Animate images with start/end frame control
- **Video Extension** - Extend existing videos with additional content
- **Multiple Aspect Ratios** - Support for 16:9, 9:16, 1:1, and more
- **Loop Videos** - Create seamlessly looping animations
- **Clarity Enhancement** - Optional video quality enhancement
- **Task Tracking** - Monitor generation progress and retrieve results

## Quick Start

### 1. Get API Token

Get your API token from [AceDataCloud Platform](https://platform.acedata.cloud):

1. Sign up or log in
2. Navigate to [Luma Videos API](https://platform.acedata.cloud/documents/5bd3597d-1ff8-44ad-a580-b66b48393e7f)
3. Click "Acquire" to get your token

### 2. Install

```bash
# Clone the repository
git clone https://github.com/AceDataCloud/mcp-luma.git
cd mcp-luma

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
mcp-luma

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
    "luma": {
      "command": "mcp-luma",
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
    "luma": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-luma", "mcp-luma"],
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
| `luma_generate_video` | Generate video from a text prompt |
| `luma_generate_video_from_image` | Generate video using reference images |
| `luma_extend_video` | Extend an existing video by ID |
| `luma_extend_video_from_url` | Extend an existing video by URL |

### Tasks

| Tool | Description |
|------|-------------|
| `luma_get_task` | Query a single task status |
| `luma_get_tasks_batch` | Query multiple tasks at once |

### Information

| Tool | Description |
|------|-------------|
| `luma_list_aspect_ratios` | List available aspect ratios |
| `luma_list_actions` | List available API actions |

## Usage Examples

### Generate Video from Prompt

```
User: Create a video of waves on a beach

Claude: I'll generate a beach wave video for you.
[Calls luma_generate_video with prompt="Ocean waves gently crashing on sandy beach, sunset"]
```

### Animate an Image

```
User: Animate this image: https://example.com/image.jpg

Claude: I'll create a video from your image.
[Calls luma_generate_video_from_image with start_image_url and appropriate prompt]
```

### Extend a Video

```
User: Continue this video with more action

Claude: I'll extend the video with additional content.
[Calls luma_extend_video with video_id and new prompt]
```

## Available Aspect Ratios

| Aspect Ratio | Description | Use Case |
|--------------|-------------|----------|
| `16:9` | Landscape (default) | YouTube, TV, presentations |
| `9:16` | Portrait | TikTok, Instagram Reels |
| `1:1` | Square | Instagram posts |
| `4:3` | Traditional | Classic video format |
| `3:4` | Portrait traditional | Portrait content |
| `21:9` | Ultrawide | Cinematic content |
| `9:21` | Tall ultrawide | Special vertical displays |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ACEDATACLOUD_API_TOKEN` | API token from AceDataCloud | **Required** |
| `ACEDATACLOUD_API_BASE_URL` | API base URL | `https://api.acedata.cloud` |
| `LUMA_DEFAULT_ASPECT_RATIO` | Default aspect ratio | `16:9` |
| `LUMA_REQUEST_TIMEOUT` | Request timeout in seconds | `180` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Command Line Options

```bash
mcp-luma --help

Options:
  --version          Show version
  --transport        Transport mode: stdio (default) or http
  --port             Port for HTTP transport (default: 8000)
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/AceDataCloud/mcp-luma.git
cd mcp-luma

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
MCPLuma/
├── core/                   # Core modules
│   ├── __init__.py
│   ├── client.py          # HTTP client for Luma API
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
├── prompts/                # MCP prompts
│   └── __init__.py        # Prompt templates
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

This server wraps the [AceDataCloud Luma API](https://platform.acedata.cloud/documents/5bd3597d-1ff8-44ad-a580-b66b48393e7f):

- [Luma Videos API](https://platform.acedata.cloud/documents/5bd3597d-1ff8-44ad-a580-b66b48393e7f) - Video generation
- [Luma Tasks API](https://platform.acedata.cloud/documents/7d32369c-4ead-4364-a4c5-652bc768b3ff) - Task queries

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
- [Luma Dream Machine](https://lumalabs.ai/dream-machine)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

---

Made with love by [AceDataCloud](https://platform.acedata.cloud)
