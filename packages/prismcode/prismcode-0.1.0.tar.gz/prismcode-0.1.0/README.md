# Prism Code

An AI coding assistant with dependency-aware context management and real-time streaming.

## Features

- **Smart Context Management** - Two-layer history system with automatic compaction
- **Dependency-Aware Focus** - Built-in dependency graph analysis to focus on relevant files
- **Real-time Streaming** - Web UI with live streaming responses and tool execution
- **File Operations** - Edit, create, read, and manage files with fuzzy matching
- **Session Management** - Persistent chat sessions with history
- **Multiple Interfaces** - Web UI, Terminal UI, or CLI

## Installation

### From PyPI (Coming Soon)

```bash
pip install prismcode
```

### From Source

```bash
git clone https://github.com/yourusername/prismcode.git
cd prismcode
uv sync
```

## Usage

### Web Interface (Recommended)

Start the web interface:

```bash
prismweb
```

Then open http://localhost:5000 in your browser.

### Terminal Interface

For a rich terminal experience:

```bash
prism
```

Commands:
- `/help` - Show available commands
- `/sessions` - List all sessions
- `/new` - Start a new session
- `/load <session_id>` - Load a previous session
- `/toggle-diff` - Toggle detailed diff display

## Configuration

Create a `.env` file in your project root:

```bash
# Required: Your LLM API key
ANTHROPIC_API_KEY=your_key_here
# or
OPENAI_API_KEY=your_key_here

# Optional: Configure default model
DEFAULT_MODEL=claude-3-5-sonnet-20241022
```

## Development

Install development dependencies:

```bash
uv sync
```

Run tests:

```bash
pytest
```

## Project Structure

- `cli/` - Terminal interface
- `core/` - Core agent logic and context management
- `tools/` - File operations and dependency analysis tools
- `prism/` - Dependency graph analysis
- `static/` & `templates/` - Web UI assets
- `run_web.py` - Web server entry point

## License

MIT License - see LICENSE file for details
