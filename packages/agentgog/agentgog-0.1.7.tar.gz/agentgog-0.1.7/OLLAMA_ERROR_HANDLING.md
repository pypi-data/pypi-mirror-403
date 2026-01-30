# Ollama Error Handling with Model Suggestions

## Overview
When using the local Ollama provider and a request fails due to a missing or unavailable model, the application now automatically fetches and displays a list of available models to help users choose the correct one.

## Implementation Details

### Enhanced Functions in `ollama_client.py`

#### 1. New Helper Function: `_get_available_models_str()`
```python
def _get_available_models_str():
    """Get a formatted string of available models"""
```
- Calls `get_available_models()` internally
- Returns a formatted list of available models
- Returns empty string if no models available or connection fails

#### 2. Updated `chat_with_ollama()`
Now handles two types of connection errors:
- **ConnectionError**: Provides helpful message to start Ollama
- **HTTPError** (404, etc.): Suggests available models
- **RequestException**: Suggests available models with usage example

#### 3. Updated `chat_classification_ollama()`
- Checks if error is model-related (contains 'model', '404', or 'not found')
- Adds available models list and usage suggestion if applicable

#### 4. Updated `chat_extraction_ollama()`
- Same enhancement as classification function
- Ensures consistent error handling across all functions

## Error Messages Format

### Before (Generic Error)
```
Error: Ollama API request failed: 404 Client Error: Not Found
```

### After (With Model Suggestions)
```
Error: Ollama API request failed: 404 Client Error: Not Found
  Available models:
    llama2
    mistral
    neural-chat
    nomic-embed-text
  Try: agentgog chat 'message' -p ollama -m mistral
```

## Usage Examples

### Scenario: User tries to use Ollama with default model, but it's not installed

**Command:**
```bash
agentgog chat "Hello" -p ollama
```

**Error Response (if llama3.2 is not available):**
```
Error: Ollama API request failed: 404 Client Error: Not Found for url: http://localhost:11434/api/chat
  Available models:
    llama2:latest
    mistral:latest
    neural-chat:latest
  Try: agentgog chat 'Hello' -p ollama -m mistral:latest
```

**User then runs:**
```bash
agentgog chat "Hello" -p ollama -m mistral:latest
```

## Error Detection Logic

The error enhancement is triggered when:
1. Request to Ollama API fails
2. Error message contains one of:
   - 'model' (case-insensitive)
   - '404' (HTTP status)
   - 'not found' (case-insensitive)

This ensures model suggestion only shows when relevant (model not found/available).

## Connection Errors

### Ollama Not Running
```
Error: Cannot connect to Ollama server at localhost:11434
Make sure Ollama is running: ollama serve
```

### Specific Suggestion
When user needs to start Ollama, the error message includes the command to run it.

## Benefits

1. **Better User Experience**: No more cryptic error messages
2. **Self-Healing**: Users can immediately see available models
3. **Reduced Support Burden**: Users can fix issues without external help
4. **Consistent Across Modes**:
   - Chat mode: Full support with suggestion
   - Classification mode: Full support with suggestion
   - Extraction mode: Full support with suggestion

## Implementation Pattern

All Ollama API functions now follow this pattern:

```python
try:
    # Make API call
    response = requests.post(OLLAMA_API_URL, ...)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    # Build error message
    error_msg = f"Ollama API error: {e}"
    
    # Try to get available models
    available_models_str = _get_available_models_str()
    if available_models_str:
        error_msg += available_models_str
        error_msg += "\n  Try: agentgog <command> -p ollama -m <model_name>"
    
    return False, None, {"error": error_msg}
```

## Testing

Run the following to test error handling:

```bash
# Test with invalid model (assuming 'nonexistent-model' doesn't exist)
agentgog chat "Hello" -p ollama -m nonexistent-model

# Test classification with invalid model
agentgog classify "Meeting tomorrow" -p ollama -m nonexistent-model

# Test with Ollama not running (connection error)
# (Stop Ollama first)
agentgog chat "Hello" -p ollama
```

## Future Enhancements

1. **Auto-suggest best model**: Rank models by size/performance
2. **Model download assistance**: Offer to download missing models
3. **Configuration persistence**: Remember user's preferred model
4. **Performance hints**: Show model specifications in suggestions
5. **Interactive model selection**: Let user choose from list interactively

## Backward Compatibility

✅ All changes are backward compatible
✅ Existing error handling still works
✅ Only enhancement is adding helpful suggestions
✅ No changes to function signatures or return types
