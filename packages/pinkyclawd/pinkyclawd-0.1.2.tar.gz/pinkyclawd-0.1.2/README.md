# PinkyClawd

```
╭──────────────────────────────────────────────────────────╮
│                                                          │
│   ██████╗ ██╗███╗   ██╗██╗  ██╗██╗   ██╗                │
│   ██╔══██╗██║████╗  ██║██║ ██╔╝╚██╗ ██╔╝                │
│   ██████╔╝██║██╔██╗ ██║█████╔╝  ╚████╔╝                 │
│   ██╔═══╝ ██║██║╚██╗██║██╔═██╗   ╚██╔╝                  │
│   ██║     ██║██║ ╚████║██║  ██╗   ██║                   │
│   ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝   ╚═╝                   │
│                                                          │
│   ██████╗██╗      █████╗ ██╗    ██╗██████╗              │
│   ██╔════╝██║     ██╔══██╗██║    ██║██╔══██╗            │
│   ██║     ██║     ███████║██║ █╗ ██║██║  ██║            │
│   ██║     ██║     ██╔══██║██║███╗██║██║  ██║            │
│   ╚██████╗███████╗██║  ██║╚███╔███╔╝██████╔╝            │
│    ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚═════╝             │
│                                                          │
│           ◢◤ AI-Powered Development ◥◣                  │
╰──────────────────────────────────────────────────────────╯
```

AI-powered development tool with TUI interface and Recursive Language Model (RLM) context management for unlimited conversation context.

## Features

- **RLM Context Management**: Automatic context archival and retrieval enables conversations beyond context window limits
- **Multi-Provider Support**: Anthropic (Claude), OpenAI (GPT-4), and more
- **Rich TUI Interface**: Full-featured terminal UI with Textual
- **14 Built-in Tools**: bash, read, write, edit, glob, grep, todo, webfetch, memory, and more
- **Session Management**: Fork, export, and manage conversation sessions
- **Slash Commands**: `/context`, `/search`, `/compact`, `/models`, `/agents`

## Installation

### via npm (recommended)

```bash
npm install -g pinkyclawd
```

### via pip

```bash
pip install pinkyclawd
```

### From source

```bash
git clone https://github.com/tekcin/PinkyClawd.git
cd PinkyClawd
pip install -e .
```

## Requirements

- Python 3.11+
- Node.js 16+ (for npm installation)

## Usage

```bash
# Start the TUI
pinkyclawd

# Start with a specific project
pinkyclawd /path/to/project

# Continue last session
pinkyclawd --continue

# Run a single command (non-interactive)
pinkyclawd run "explain this codebase"

# List available models
pinkyclawd models
```

## Configuration

Create `~/.config/pinkyclawd/pinkyclawd.json`:

```json
{
  "model": "anthropic/claude-sonnet-4",
  "theme": "pinkyclawd",
  "rlm": {
    "enabled": true,
    "threshold_ratio": 0.33,
    "auto_retrieve": true
  }
}
```

## Environment Variables

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
```

## RLM (Recursive Language Model)

RLM enables unlimited context by automatically:

1. **Tracking** token usage across the conversation
2. **Archiving** older context when threshold is reached (default: 33%)
3. **Retrieving** relevant archived context for new queries
4. **Injecting** context into the conversation seamlessly

### Manual RLM Commands

- `/context` - Show current token usage
- `/search <query>` - Search archived context
- `/compact` - Manually trigger context archival

### RLM Tools

- `memory` - Search and retrieve archived context
- `rlm_query` - Execute Python queries on archived context

## License

MIT

## Author

Michael Thornton (tekcin@yahoo.com)
