#!/usr/bin/env python3
"""
Shared OpenRouter API client module

Provides common functionality for interacting with OpenRouter API
across all classifier modules.
"""
import requests
import json
import os
import logging

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "x-ai/grok-4.1-fast"


def get_api_key():
    """
    Retrieve OpenRouter API key from environment or file

    Returns:
        str: API key or None if not found
    """
    api_key = os.environ.get('OPENROUTER_API_KEY')

    if not api_key:
        key_file = os.path.expanduser('~/.openai_openrouter.key')
        try:
            if os.path.isfile(key_file):
                with open(key_file, 'r') as f:
                    api_key = f.read().strip()
                    if api_key:
                        logger.debug(f"Loaded API key from {key_file}")
        except Exception as e:
            logger.warning(f"Failed to read API key from {key_file}: {e}")

    return api_key


def chat_with_openrouter(message=None, system_prompt=None, timeout=10, model=None, messages=None):
    """
    Send a chat message to OpenRouter API

    Args:
        message: User message content (optional if messages provided)
        system_prompt: System prompt for the AI (optional if messages provided)
        timeout: API request timeout in seconds (default: 10)
        model: Model to use (default: OPENROUTER_MODEL)
        messages: Full conversation history list of message dicts (optional)
                  If provided, message and system_prompt are ignored

    Returns:
        tuple: (success: bool, content: str or None, raw_response: dict)
    """
    api_key = get_api_key()

    if not api_key:
        logger.error("OPENROUTER_API_KEY environment variable not set and ~/.openai_openrouter.key not found")
        return False, None, {"error": "Missing API key"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    if messages:
        conversation_messages = messages
    else:
        if not message or not message.strip():
            logger.warning("Empty message text provided")
            return False, None, {"error": "Empty message"}

        conversation_messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": message
            }
        ]

    payload = {
        "model": model or OPENROUTER_MODEL,
        "messages": conversation_messages
    }

    try:
        if message:
            logger.info(f"Sending message to OpenRouter: {message[:100]}...")
        elif messages:
            last_message = messages[-1] if messages and len(messages) > 0 else {}
            logger.info(f"Sending conversation with {len(messages)} messages. Last: {last_message.get('content', '')[:100]}...")
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()

        response_data = response.json()

        try:
            content = response_data['choices'][0]['message']['content'].strip()
            logger.info(f"Received response: {content[:100]}...")
            return True, content, response_data

        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract content from response: {e}")
            return False, None, response_data

    except requests.exceptions.Timeout:
        logger.error(f"OpenRouter API request timed out after {timeout}s")
        return False, None, {"error": "Timeout"}

    except requests.exceptions.RequestException as e:
        logger.error(f"OpenRouter API request failed: {e}")
        return False, None, {"error": str(e)}

    except Exception as e:
        logger.error(f"Unexpected error during chat: {e}", exc_info=True)
        return False, None, {"error": str(e)}


def chat_classification(message, system_prompt, timeout=10, model=None):
    """
    Send a classification request to OpenRouter API
    Returns a single word/token response

    Args:
        message: User message to classify
        system_prompt: System prompt defining classification rules
        timeout: API request timeout in seconds (default: 10)
        model: Model to use (default: OPENROUTER_MODEL)

    Returns:
        tuple: (success: bool, classification: str or None, raw_response: dict)
    """
    success, content, raw_response = chat_with_openrouter(
        message=message,
        system_prompt=system_prompt,
        timeout=timeout,
        model=model
    )

    if success and content:
        return True, content, raw_response
    return False, None, raw_response


def chat_extraction(message, system_prompt, timeout=10, model=None):
    """
    Send an extraction request to OpenRouter API
    Returns JSON-parsed response

    Args:
        message: User message to extract from
        system_prompt: System prompt defining extraction rules
        timeout: API request timeout in seconds (default: 10)
        model: Model to use (default: OPENROUTER_MODEL)

    Returns:
        tuple: (success: bool, data: dict or None, raw_response: dict)
    """
    success, content, raw_response = chat_with_openrouter(
        message=message,
        system_prompt=system_prompt,
        timeout=timeout,
        model=model
    )

    if not success or not content:
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
