# cli-edit

A terminal-based code editor that uses AI to apply natural language edits to your files. Describe what you want changed, preview the diff, and accept or reject.

## Install

```bash
pip install cli-edit
```

Or install from source:

```bash
git clone https://github.com/amgustav/cli-edit.git
cd cli-edit
pip install -e .
```

## Setup

Set your API key:

```bash
export ANTHROPIC_API_KEY="your-key-here"
# or
export OPENAI_API_KEY="your-key-here"
```

## Usage

```bash
# Open a file for editing
cli-edit main.py

# Start with a specific prompt
cli-edit main.py --prompt "add error handling to the fetch function"

# Use a specific model
cli-edit main.py --model claude-sonnet

# Non-interactive mode (auto-accept)
cli-edit main.py --prompt "fix the bug" --yes

# Disable backup
cli-edit main.py --no-backup

# More context lines in diff
cli-edit main.py --context-lines 5
```

## How It Works

1. Run `cli-edit <file>` - the file is displayed with syntax highlighting
2. Type a description of the changes you want
3. The AI generates edits and a diff is displayed
4. Choose an action:
   - **a** - Accept the changes
   - **r** - Reject and try a different prompt
   - **e** - Edit your prompt and retry
   - **u** - Undo the last accepted change
   - **q** - Quit

## Configuration

Create `~/.config/cli-edit/config.toml`:

```toml
model = "claude-sonnet"
theme = "monokai"
context_lines = 3
backup_enabled = true
streaming = true
```

Or add `.cli-edit.toml` to your project root for per-project settings.

## Supported Models

| Shorthand | Model | Provider |
|-----------|-------|----------|
| `claude-sonnet` | Claude Sonnet (default) | Anthropic |
| `claude-haiku` | Claude Haiku | Anthropic |
| `claude-opus` | Claude Opus | Anthropic |
| `gpt-4o` | GPT-4o | OpenAI |
| `gpt-4o-mini` | GPT-4o Mini | OpenAI |

## Options

```
Usage: cli-edit [OPTIONS] FILE

Options:
  -m, --model TEXT          AI model to use
  -p, --prompt TEXT         Edit prompt (skips interactive prompt)
  -y, --yes                 Auto-accept changes
  --no-backup               Skip creating a backup file
  -c, --context-lines INT   Context lines in diff
  -t, --theme TEXT          Syntax highlighting theme
  --no-stream               Disable response streaming
  -v, --verbose             Enable debug logging
  --version                 Show version
  --help                    Show this message and exit
```

## Development

```bash
pip install -e ".[dev]"
pytest
mypy src
ruff check src tests
```

## License

MIT
