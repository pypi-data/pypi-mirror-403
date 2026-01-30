# Provider Switching Quick Start

## One-Liner Examples

### Using Ollama (Local Inference)
```bash
# Classification
agentgog classify "Meeting tomorrow" -p ollama

# Chat
agentgog chat "Hello" -p ollama

# Chat with specific model
agentgog chat "Hi" -p ollama -m mistral

# Interactive chat
agentgog chat -i -p ollama
```

### Using OpenRouter (Cloud, Default)
```bash
# Classification (default provider, no -p needed)
agentgog classify "Meeting tomorrow"

# Chat
agentgog chat "What's AI?"

# Chat with specific model
agentgog chat "Explain quantum physics" -m x-ai/grok-4.1-fast

# Interactive chat
agentgog chat -i
```

## Key Points

1. **Default Provider**: OpenRouter
   - If you don't specify `-p`, OpenRouter is used
   - Requires `OPENROUTER_API_KEY` environment variable

2. **Ollama Support**:
   - Use `-p ollama` to switch to local Ollama
   - Requires Ollama running on `localhost:11434`
   - No API keys needed

3. **Model Selection**:
   - OpenRouter: Use with `-m` option (e.g., `-m x-ai/grok-4.1-fast`)
   - Ollama: Use with `-m` option (e.g., `-m llama2`, `-m mistral`)
   - Default models used if not specified

## Provider Options
- `-p openrouter` - Use OpenRouter (cloud-based, default)
- `-p ollama` - Use local Ollama instance

## Help
```bash
agentgog classify --help      # See all options
agentgog chat --help
agentgog translator --help
```
