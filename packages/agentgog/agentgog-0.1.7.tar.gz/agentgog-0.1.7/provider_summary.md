# Provider and Module Summary for AgentGog

This document summarizes the AI providers, modes of work, and underlying Python modules used in the AgentGog project.

## Summary Table

| Mode of Work | Provider | Underlying Module | Module File | Description |
|--------------|----------|-------------------|-------------|-------------|
| **Classification** | OpenRouter | `requests` (direct API) | `openrouter_client.py` | Classifies messages into CALENDAR/TASK/MEMO categories |
| **Chat** | OpenRouter | `requests` (direct API) | `openrouter_client.py` | General AI chat functionality |
| **Calendar Extraction** | OpenRouter | `requests` (via `openrouter_client.py`) | `calendar_extractor.py` | Extracts calendar event details from text |
| **Task Extraction** | OpenRouter | `requests` (via `openrouter_client.py`) | `task_extractor.py` | Extracts task details from text |
| **Memo Extraction** | OpenRouter | `requests` (via `openrouter_client.py`) | `memo_extractor.py` | Extracts memo details from text |
| **Translator** | OpenRouter | `smolagents` (OpenAIModel) | `smol_translator.py` | Translates SRT subtitles using CodeAgent |
| **QR Payment** | OpenRouter | `smolagents` (OpenAIModel) | `smol_qrpayment.py` | Generates QR payment codes using CodeAgent |
| **CodeAgent** | OpenRouter | `smolagents` (OpenAIModel) | `smol_codeagent.py` | Vanilla CodeAgent with built-in prompt for general tasks |

## Architecture Details

### Direct API Calls
Most modules use direct OpenRouter API calls via the shared `openrouter_client.py` module:
- Classification (`chat_classification`)
- Chat (`chat_with_openrouter`) 
- Extraction (`chat_extraction`)

### Smolagents Integration
Two modules use the `smolagents` framework with OpenRouter:
- **Translator**: Uses `CodeAgent` with `OpenAIModel` for SRT translation
- **QR Payment**: Uses `CodeAgent` with `OpenAIModel` for payment QR generation

### Provider Configuration
All modules consistently use OpenRouter as the AI provider:
- API endpoint: `https://openrouter.ai/api/v1`
- Authentication via `OPENROUTER_API_KEY` environment variable
- Default model: `x-ai/grok-4.1-fast` (configurable per module)

### External Integrations
- **Calendar**: Google Calendar API (via `googleapiclient`)
- **Tasks**: Google Tasks API (via `googleapiclient`) 
- **Memos**: Simplenote API (via `simplenote` Python package)
- **QR Codes**: `qrcode` Python package for QR generation

## File Dependencies

```
src/agentgog/
├── cli.py                    # Main CLI interface
├── openrouter_client.py      # Shared OpenRouter client
├── ai_classifier.py          # Classification logic
├── calendar_extractor.py     # Calendar extraction
├── task_extractor.py         # Task extraction  
├── memo_extractor.py         # Memo extraction
├── smol_translator.py        # SRT translation (smolagents)
├── smol_qrpayment.py         # QR payment generation (smolagents)
├── smol_codeagent.py         # Vanilla CodeAgent for general tasks
└── smol_common.py           # Shared utilities for smolagents modules
```

## Model Usage

- **Free models available**: `google/gemma-3-27b-it:free`, `xiaomi/mimo-v2-flash:free`, `nex-agi/deepseek-v3.1-nex-n1:free`
- **Default model**: `x-ai/grok-4.1-fast` (paid)
- **Smolagents modules**: Default to first free model in list
- **CodeAgent**: Uses vanilla CodeAgent with built-in system prompt (no custom prompt)

## Key Insights

1. **Consistent Provider**: All AI operations use OpenRouter exclusively
2. **Two Approaches**: Direct API calls for simple tasks, smolagents for complex multi-step operations
3. **Modular Design**: Shared `openrouter_client.py` reduces code duplication
4. **External Services**: Integration with Google services and Simplenote for data persistence
5. **Model Flexibility**: Support for both free and paid models with easy configuration