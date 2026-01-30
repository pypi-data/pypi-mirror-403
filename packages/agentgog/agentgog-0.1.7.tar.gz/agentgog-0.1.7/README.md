# agentgog

CLI assistant that classifies short messages into **CALENDAR**, **TASK**, or **MEMO** and then:

- **CALENDAR** → extracts event details and inserts into **Google Calendar**
- **TASK** → extracts task details and inserts into **Google Tasks**
- **MEMO** → extracts memo details and saves to **Simplenote**

It also provides a general **chat** command, plus extra utilities (**translator**, **qrpayment**, **codeagent**).

## Install

This repo uses `uv`.

```bash
uv sync
```

Run from source:

```bash
uv run agentgog --help
```

## AI Provider setup

### OpenRouter (default)

Set API key via env var (preferred):

```bash
export OPENROUTER_API_KEY="<your_key>"
```

Or put the key in:

- `~/.openai_openrouter.key`

### Ollama (local)

Install and start Ollama:

```bash
ollama serve
```

Then use `-p ollama`.

## Google setup (Calendar + Tasks)

1. Create OAuth client credentials in Google Cloud Console.
2. Save the JSON to:

- `~/.config/google/credentials.json`

On first run, a browser window opens for authorization and a token is cached at:

- `~/.config/google/token.json`

If you ever change scopes and get “insufficient authentication scopes”, delete the token and re-run:

```bash
rm -f ~/.config/google/token.json
```

## Simplenote setup (MEMO)

Set credentials via environment variables:

```bash
export SIMPLENOTE_LOCAL_USER="user@example.com"
export SIMPLENOTE_LOCAL_PASSWORD="<your_password>"
```

## Usage

### Classify and execute

```bash
# Calendar event → Google Calendar
uv run agentgog classify "Meeting with Alice tomorrow at 10am"

# Task → Google Tasks (list: "My Tasks"; falls back to default)
uv run agentgog classify "Buy groceries tomorrow"

# Memo → Simplenote
uv run agentgog classify "Remember that my passport number is 123456789"
```

### Choose provider

```bash
# Use OpenRouter explicitly
uv run agentgog classify "Buy groceries" -p openrouter

# Use local Ollama
uv run agentgog classify "Buy groceries" -p ollama
```

### Chat

Single prompt:

```bash
uv run agentgog chat "Explain the difference between TCP and UDP"
```

Interactive chat (keeps conversation history in-memory):

```bash
uv run agentgog chat -i
```

Interactive commands:
- Quit: `/q`, `/quit`, `/exit`, `quit`, `exit`
- Clear conversation: `/c`, `/clear`, `/reset`, `/r`

Input line editing + persistent command history:
- History file: `~/.agentgog_history`

### Translator (SRT → Czech)

Uses `smolagents` (OpenRouter only):

```bash
uv run agentgog translator -s subtitles.srt -m google/gemma-3-27b-it:free
```

### QR payment

Uses `smolagents` (OpenRouter only):

```bash
uv run agentgog qrpayment "Transfer 500 CZK to account 1234567890/0300" -m google/gemma-3-27b-it:free
```

### Code agent

Uses `smolagents`:

```bash
uv run agentgog codeagent "Write a Python function to compute fibonacci" -m google/gemma-3-27b-it:free -x 10
```

## Logging

- Log file: `~/agentgog.log`
