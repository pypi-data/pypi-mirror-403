# agentgog tasks/status

This file tracks what’s implemented and working.

## Project goal

Turn short messages into actions by:
- Classifying them into **CALENDAR**, **TASK**, **MEMO**
- Extracting structured details
- Sending them to external systems (Calendar / Tasks / notes)

## Current functionality (working)

### CLI commands

- `agentgog classify "..."`
  - Runs the classifier and triggers the relevant action:
    - `CALENDAR` → Google Calendar insert
    - `TASK` → Google Tasks insert (tries list name `My Tasks`, otherwise falls back to `@default`)
    - `MEMO` → Simplenote note creation
  - Supports provider switch: `-p openrouter|ollama`

- `agentgog chat "..."`
  - General chat.
  - Supports provider switch: `-p openrouter|ollama`
  - `-i` starts interactive mode with:
    - Conversation memory (in-memory)
    - Line editing + persistent command history via `prompt_toolkit` (`~/.agentgog_history`)
    - Commands: `/q` quit, `/c` clear history

- `agentgog translator -s file.srt -m <model>`
  - SRT → Czech translation using `smolagents` (OpenRouter only).

- `agentgog qrpayment "..." -m <model>`
  - Generates a QR payment code (OpenRouter only).

- `agentgog codeagent "..." -m <model>`
  - Runs a CodeAgent flow (provider option exists; behavior depends on `smolagents`).

### Providers

- **OpenRouter** (default)
  - Uses `OPENROUTER_API_KEY` (or `~/.openai_openrouter.key`).

- **Ollama** (local)
  - `-p ollama`
  - Enhanced error handling suggests installed models when the requested model is missing.

### Integrations

- **Google Calendar**
  - OAuth credentials file: `~/.config/google/credentials.json`
  - Token cache: `~/.config/google/token.json`
  - Inserts event into `primary` calendar.

- **Google Tasks**
  - Uses the same token file (`~/.config/google/token.json`).
  - Important: token must include Tasks scope.

- **Simplenote (MEMO)**
  - Requires environment variables:
    - `SIMPLENOTE_LOCAL_USER`
    - `SIMPLENOTE_LOCAL_PASSWORD`

## Known constraints / notes

- If you change Google OAuth scopes (e.g. add Tasks), delete token and re-auth:
  - `rm -f ~/.config/google/token.json`

- Some utilities (translator/qrpayment) are OpenRouter-only today.

## Useful one-liners

```bash
# Calendar
uv run agentgog classify "Meeting tomorrow at 10am"

# Task
uv run agentgog classify "Buy groceries tomorrow"

# Memo
uv run agentgog classify "Remember that my passport number is 123456789"

# Chat interactive
uv run agentgog chat -i
```
