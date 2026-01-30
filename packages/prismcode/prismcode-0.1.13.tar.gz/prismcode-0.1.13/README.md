# Prism Code

An AI coding assistant with dependency-aware context management and real-time streaming.

## Features

- **Smart Context Management** - Two-layer history system with automatic compaction.
- **Dependency-Aware Focus** - Built-in dependency graph analysis.
- **Real-time Streaming** - Modern Web Workspace with live tool execution.
- **Multi-Project Support** - Seamlessly switch between local and SSH projects.

## Installation

### For Users (pip)
```bash
pip install prismcode
prismweb
```

### For Developers (uv)
We recommend using `uv` for the fastest and most reliable development environment.

1. **Install uv**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. **Setup environment**:
   ```bash
   git clone https://github.com/Jimmys-Code/Prism.git
   cd Prism
   uv venv
   source .venv/bin/activate
   uv sync
   ```

## Usage

### Web Workspace (Recommended)
```bash
prismweb
```
Open [http://localhost:5000](http://localhost:5000).

### CLI / TUI
```bash
prism
```

## Configuration

Create a `.env` file in the project root:

```bash
# Required: One or more API keys
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here

# Optional: Set preferred model
# DEFAULT_MODEL=claude-3-5-sonnet-20241022
```

## License
Proprietary - All rights reserved.
