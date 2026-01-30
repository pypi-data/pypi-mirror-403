#!/usr/bin/env python3
"""
Shared Ollama API client module

Provides common functionality for interacting with local Ollama API
across all classifier modules.
"""
import requests
import json
import os
import logging

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_API_URL = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_MODEL = "llama3.2"  # Default model for Ollama


def get_available_models():
    """
    Get list of available models from Ollama

    Returns:
        tuple: (success: bool, models: list or None, raw_response: dict)
    """
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        response.raise_for_status()
        
        response_data = response.json()
        models = [model['name'] for model in response_data.get('models', [])]
        
        logger.info(f"Found {len(models)} available models")
        return True, models, response_data
        
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to Ollama server at localhost:11434")
        return False, None, {"error": "Connection failed - Ollama not running?"}
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch models from Ollama: {e}")
        return False, None, {"error": str(e)}
    
    except Exception as e:
        logger.error(f"Unexpected error fetching models: {e}", exc_info=True)
        return False, None, {"error": str(e)}


def get_running_models():
    """
    Get list of currently running models from Ollama

    Returns:
        tuple: (success: bool, models: list or None, raw_response: dict)
    """
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/ps", timeout=5)
        response.raise_for_status()
        
        response_data = response.json()
        running_models = []
        
        for model in response_data.get('models', []):
            running_models.append({
                'name': model['name'],
                'size': model.get('size', 0),
                'status': model.get('status', 'unknown'),
                'expires_at': model.get('expires_at')
            })
        
        logger.info(f"Found {len(running_models)} running models")
        return True, running_models, response_data
        
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to Ollama server at localhost:11434")
        return False, None, {"error": "Connection failed - Ollama not running?"}
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch running models from Ollama: {e}")
        return False, None, {"error": str(e)}
    
    except Exception as e:
        logger.error(f"Unexpected error fetching running models: {e}", exc_info=True)
        return False, None, {"error": str(e)}


def _get_available_models_str():
    """
    Get a formatted string of available models

    Returns:
        str: Formatted list of available models or empty string
    """
    success, models, _ = get_available_models()
    if success and models:
        return "\n  Available models:\n    " + "\n    ".join(models)
    return ""


def chat_with_ollama(message=None, system_prompt=None, timeout=90, model=None, messages=None):
    """
    Send a chat message to Ollama API

    Args:
        message: User message content (optional if messages provided)
        system_prompt: System prompt for the AI (optional if messages provided)
        timeout: API request timeout in seconds (default: 30)
        model: Model to use (default: OLLAMA_MODEL)
        messages: Full conversation history list of message dicts (optional)
                  If provided, message and system_prompt are ignored

    Returns:
        tuple: (success: bool, content: str or None, raw_response: dict)
    """
    if messages:
        conversation_messages = messages
    else:
        if not message or not message.strip():
            logger.warning("Empty message text provided")
            return False, None, {"error": "Empty message"}

        conversation_messages = []
        
        if system_prompt:
            conversation_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        conversation_messages.append({
            "role": "user",
            "content": message
        })

    payload = {
        "model": model or OLLAMA_MODEL,
        "messages": conversation_messages,
        "stream": False  # We want complete response, not streaming
    }

    try:
        if message:
            logger.info(f"Sending message to Ollama: {message[:100]}...")
        elif messages:
            last_message = messages[-1] if messages and len(messages) > 0 else {}
            logger.info(f"Sending conversation with {len(messages)} messages. Last: {last_message.get('content', '')[:100]}...")
        
        response = requests.post(
            OLLAMA_API_URL,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()

        response_data = response.json()

        try:
            content = response_data['message']['content'].strip()
            logger.info(f"Received response: {content[:100]}...")
            return True, content, response_data

        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract content from response: {e}")
            return False, None, response_data

    except requests.exceptions.Timeout:
        logger.error(f"Ollama API request timed out after {timeout}s")
        return False, None, {"error": "Timeout"}

    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to Ollama server at localhost:11434")
        error_msg = "Cannot connect to Ollama server at localhost:11434\nMake sure Ollama is running: ollama serve"
        return False, None, {"error": error_msg}

    except requests.exceptions.HTTPError as e:
        # Handle model not found or other HTTP errors
        logger.error(f"Ollama API HTTP error: {e}")
        error_msg = f"Ollama API error: {e}"
        
        # Try to get available models for suggestion
        available_models_str = _get_available_models_str()
        if available_models_str:
            error_msg += available_models_str
            error_msg += "\n  Try: agentgog chat 'message' -p ollama -m <model_name>"
        
        return False, None, {"error": error_msg}

    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama API request failed: {e}")
        error_msg = f"Ollama API request failed: {e}"
        
        # Try to get available models for suggestion
        available_models_str = _get_available_models_str()
        if available_models_str:
            error_msg += available_models_str
            error_msg += "\n  Try: agentgog chat 'message' -p ollama -m <model_name>"
        
        return False, None, {"error": error_msg}

    except Exception as e:
        logger.error(f"Unexpected error during chat: {e}", exc_info=True)
        return False, None, {"error": str(e)}


def chat_classification_ollama(message, system_prompt, timeout=90, model=None):
    """
    Send a classification request to Ollama API
    Returns a single word/token response

    Args:
        message: User message to classify
        system_prompt: System prompt defining classification rules
        timeout: API request timeout in seconds (default: 30)
        model: Model to use (default: OLLAMA_MODEL)

    Returns:
        tuple: (success: bool, classification: str or None, raw_response: dict)
    """
    success, content, raw_response = chat_with_ollama(
        message=message,
        system_prompt=system_prompt,
        timeout=timeout,
        model=model
    )

    if success and content:
        return True, content, raw_response
    
    # Enhance error message with available models if classification fails
    if not success and raw_response and 'error' in raw_response:
        error = raw_response['error']
        if 'model' in error.lower() or '404' in str(error) or 'not found' in error.lower():
            available_models_str = _get_available_models_str()
            if available_models_str:
                error += available_models_str
                error += "\n  Try: agentgog classify 'message' -p ollama -m <model_name>"
                raw_response['error'] = error
    
    return False, None, raw_response


def chat_extraction_ollama(message, system_prompt, timeout=90, model=None):
    """
    Send an extraction request to Ollama API
    Returns JSON-parsed response

    Args:
        message: User message to extract from
        system_prompt: System prompt defining extraction rules
        timeout: API request timeout in seconds (default: 30)
        model: Model to use (default: OLLAMA_MODEL)

    Returns:
        tuple: (success: bool, data: dict or None, raw_response: dict)
    """
    success, content, raw_response = chat_with_ollama(
        message=message,
        system_prompt=system_prompt,
        timeout=timeout,
        model=model
    )

    if not success or not content:
        # Enhance error message with available models if extraction fails
        if not success and raw_response and 'error' in raw_response:
            error = raw_response['error']
            if 'model' in error.lower() or '404' in str(error) or 'not found' in error.lower():
                available_models_str = _get_available_models_str()
                if available_models_str:
                    error += available_models_str
                    error += "\n  Try: agentgog classify 'message' -p ollama -m <model_name>"
                    raw_response['error'] = error
        
        return False, None, raw_response

    try:
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '').strip()
        elif content.startswith('```'):
            content = content.replace('```', '').strip()

        data = json.loads(content)

        if not isinstance(data, dict):
            raise ValueError("Expected JSON object")

        logger.info(f"Successfully parsed extraction data")
        return True, data, raw_response

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse extraction response: {e}")
        return False, None, raw_response


def test_ollama_connection():
    """
    Test Ollama connection and get basic info

    Returns:
        tuple: (success: bool, info: dict or None, raw_response: dict)
    """
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/version", timeout=5)
        response.raise_for_status()
        
        version_info = response.json()
        logger.info("Ollama connection successful")
        
        return True, version_info, version_info
        
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to Ollama server at localhost:11434")
        return False, None, {"error": "Connection failed - Ollama not running?"}
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        return False, None, {"error": str(e)}
    
    except Exception as e:
        logger.error(f"Unexpected error testing Ollama connection: {e}", exc_info=True)
        return False, None, {"error": str(e)}