# Provider Support Update

## Summary
All work modes now support switching between OpenRouter and local Ollama providers using the `--provider` or `-p` option.

## Changes Made

### 1. New Provider Abstraction Layer (`src/agentgog/provider.py`)
Created a unified interface for provider switching with the following features:
- **Constants**: `PROVIDER_OPENROUTER` and `PROVIDER_OLLAMA`
- **Validation**: `validate_provider()` function to check provider names
- **Unified Functions**:
  - `chat_with_provider()` - unified chat interface
  - `classify_with_provider()` - unified classification interface
  - `extract_with_provider()` - unified extraction interface
  - `get_default_model()` - provider-specific default models
  - `get_chat_function()`, `get_classification_function()`, `get_extraction_function()` - get provider-specific functions

### 2. Updated Classifier Modules
Modified the following modules to support provider parameter:
- **ai_classifier.py**: `classify_message()` and `classify_message_simple()` now accept `provider` parameter
- **calendar_extractor.py**: `extract_calendar_details()` now accepts `provider` parameter
- **task_extractor.py**: `extract_task_details()` now accepts `provider` parameter
- **memo_extractor.py**: `extract_memo_details()` now accepts `provider` parameter

All default to OpenRouter (`PROVIDER_OPENROUTER`) for backward compatibility.

### 3. Updated CLI Commands
All CLI commands now support the `--provider` or `-p` option:

#### Commands with Full Provider Support
- **classify**: `agentgog classify "message" -p ollama`
- **chat**: `agentgog chat "message" -p ollama`

#### Commands with OpenRouter-Only Support (placeholder)
- **translator**: `agentgog translator -s file.srt --model <model> -p openrouter`
- **qrpayment**: `agentgog qrpayment "prompt" --model <model> -p openrouter`
- **codeagent**: `agentgog codeagent "prompt" --model <model> -p openrouter`

These commands currently only support OpenRouter (use `smolagents` which is OpenRouter-based).

## Provider Configuration

### OpenRouter (Default)
- **Provider name**: `openrouter`
- **Default model**: `x-ai/grok-4.1-fast`
- **Configuration**: API key from environment variable `OPENROUTER_API_KEY` or `~/.openai_openrouter.key`

### Ollama (Local)
- **Provider name**: `ollama`
- **Default model**: `llama3.2`
- **Configuration**: Connects to local Ollama server at `http://localhost:11434`

## Usage Examples

### Classification
```bash
# Using OpenRouter (default)
agentgog classify "Meeting tomorrow at 10am"

# Using local Ollama
agentgog classify "Meeting tomorrow at 10am" -p ollama
```

### Chat
```bash
# Using OpenRouter (default)
agentgog chat "What's the capital of France?"

# Using local Ollama with specific model
agentgog chat "Hello" -p ollama -m llama2

# Interactive mode with Ollama
agentgog chat -i -p ollama
```

### Translator (OpenRouter only)
```bash
agentgog translator -s subtitles.srt --model google/gemma-3-27b-it:free -p openrouter
```

## Error Handling
- Invalid provider names are rejected with a clear error message
- Provider validation is performed before executing commands
- Provider-specific timeout defaults are applied:
  - OpenRouter: 10 seconds
  - Ollama: 30 seconds

## Backward Compatibility
- All changes are backward compatible
- Default provider is OpenRouter for all commands
- Existing scripts without `--provider` option will continue to work as before
- Provider parameter is optional with sensible defaults

## Testing
Run the following command to verify the implementation:
```bash
uv run src/agentgog/cli.py classify --help
uv run src/agentgog/cli.py chat --help
```

All commands should show the `-p, --provider TEXT` option in their help output.
