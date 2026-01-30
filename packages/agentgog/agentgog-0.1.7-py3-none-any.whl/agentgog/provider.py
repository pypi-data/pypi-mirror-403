#!/usr/bin/env python3
"""
Provider abstraction layer for AI backend switching

Supports both OpenRouter and local Ollama providers with a unified interface.
"""
import logging
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Provider types
PROVIDER_OPENROUTER = "openrouter"
PROVIDER_OLLAMA = "ollama"

# Default provider
DEFAULT_PROVIDER = PROVIDER_OPENROUTER

# Default models per provider
DEFAULT_MODELS = {
    PROVIDER_OPENROUTER: "x-ai/grok-4.1-fast",
    PROVIDER_OLLAMA: "llama3.2"
}

# Default timeouts per provider (in seconds)
DEFAULT_TIMEOUT_OLLAMA = 90
DEFAULT_TIMEOUT_OPENROUTER = 10


def get_chat_function(provider: str = DEFAULT_PROVIDER):
    """
    Get the chat function for the specified provider
    
    Args:
        provider: Provider name ('openrouter' or 'ollama')
    
    Returns:
        The chat function from the provider module
    """
    if provider == PROVIDER_OLLAMA:
        from ollama_client import chat_with_ollama
        return chat_with_ollama
    else:
        from openrouter_client import chat_with_openrouter
        return chat_with_openrouter


def get_classification_function(provider: str = DEFAULT_PROVIDER):
    """
    Get the classification function for the specified provider
    
    Args:
        provider: Provider name ('openrouter' or 'ollama')
    
    Returns:
        The classification function from the provider module
    """
    if provider == PROVIDER_OLLAMA:
        from ollama_client import chat_classification_ollama
        return chat_classification_ollama
    else:
        from openrouter_client import chat_classification
        return chat_classification


def get_extraction_function(provider: str = DEFAULT_PROVIDER):
    """
    Get the extraction function for the specified provider
    
    Args:
        provider: Provider name ('openrouter' or 'ollama')
    
    Returns:
        The extraction function from the provider module
    """
    if provider == PROVIDER_OLLAMA:
        from ollama_client import chat_extraction_ollama
        return chat_extraction_ollama
    else:
        from openrouter_client import chat_extraction
        return chat_extraction


def get_default_model(provider: str = DEFAULT_PROVIDER) -> str:
    """
    Get the default model for the specified provider
    
    Args:
        provider: Provider name ('openrouter' or 'ollama')
    
    Returns:
        Default model name for the provider
    """
    return DEFAULT_MODELS.get(provider, DEFAULT_MODELS[DEFAULT_PROVIDER])


def validate_provider(provider: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if the provider is supported
    
    Args:
        provider: Provider name to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_providers = [PROVIDER_OPENROUTER, PROVIDER_OLLAMA]
    
    if provider not in valid_providers:
        return False, f"Invalid provider '{provider}'. Must be one of: {', '.join(valid_providers)}"
    
    return True, None


def chat_with_provider(
    provider: str = DEFAULT_PROVIDER,
    message: Optional[str] = None,
    system_prompt: Optional[str] = None,
    timeout: Optional[int] = None,
    model: Optional[str] = None,
    messages: Optional[list] = None
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Unified interface for chatting with any provider
    
    Args:
        provider: Provider name ('openrouter' or 'ollama')
        message: User message content (optional if messages provided)
        system_prompt: System prompt for the AI (optional if messages provided)
        timeout: API request timeout in seconds (provider-specific defaults)
        model: Model to use (provider-specific defaults if not specified)
        messages: Full conversation history list of message dicts (optional)
    
    Returns:
        tuple: (success: bool, content: str or None, raw_response: dict)
    """
    is_valid, error_msg = validate_provider(provider)
    if not is_valid:
        logger.error(error_msg)
        return False, None, {"error": error_msg}
    
    chat_func = get_chat_function(provider)
    
    # Use provider-specific timeout defaults if not specified
    if timeout is None:
        timeout = DEFAULT_TIMEOUT_OLLAMA if provider == PROVIDER_OLLAMA else DEFAULT_TIMEOUT_OPENROUTER
    
    # Use default model if not specified
    if model is None:
        model = get_default_model(provider)
    
    return chat_func(
        message=message,
        system_prompt=system_prompt,
        timeout=timeout,
        model=model,
        messages=messages
    )


def classify_with_provider(
    provider: str = DEFAULT_PROVIDER,
    message: Optional[str] = None,
    system_prompt: Optional[str] = None,
    timeout: Optional[int] = None,
    model: Optional[str] = None
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Unified interface for classification with any provider
    
    Args:
        provider: Provider name ('openrouter' or 'ollama')
        message: Message to classify
        system_prompt: System prompt defining classification rules
        timeout: API request timeout in seconds (provider-specific defaults)
        model: Model to use (provider-specific defaults if not specified)
    
    Returns:
        tuple: (success: bool, classification: str or None, raw_response: dict)
    """
    is_valid, error_msg = validate_provider(provider)
    if not is_valid:
        logger.error(error_msg)
        return False, None, {"error": error_msg}
    
    classify_func = get_classification_function(provider)
    
    # Use provider-specific timeout defaults if not specified
    if timeout is None:
        timeout = DEFAULT_TIMEOUT_OLLAMA if provider == PROVIDER_OLLAMA else DEFAULT_TIMEOUT_OPENROUTER
    
    # Use default model if not specified
    if model is None:
        model = get_default_model(provider)
    
    return classify_func(
        message=message,
        system_prompt=system_prompt,
        timeout=timeout,
        model=model
    )


def extract_with_provider(
    provider: str = DEFAULT_PROVIDER,
    message: Optional[str] = None,
    system_prompt: Optional[str] = None,
    timeout: Optional[int] = None,
    model: Optional[str] = None
) -> Tuple[bool, Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Unified interface for extraction with any provider
    
    Args:
        provider: Provider name ('openrouter' or 'ollama')
        message: Message to extract from
        system_prompt: System prompt defining extraction rules
        timeout: API request timeout in seconds (provider-specific defaults)
        model: Model to use (provider-specific defaults if not specified)
    
    Returns:
        tuple: (success: bool, data: dict or None, raw_response: dict)
    """
    is_valid, error_msg = validate_provider(provider)
    if not is_valid:
        logger.error(error_msg)
        return False, None, {"error": error_msg}
    
    extract_func = get_extraction_function(provider)
    
    # Use provider-specific timeout defaults if not specified
    if timeout is None:
        timeout = DEFAULT_TIMEOUT_OLLAMA if provider == PROVIDER_OLLAMA else DEFAULT_TIMEOUT_OPENROUTER
    
    # Use default model if not specified
    if model is None:
        model = get_default_model(provider)
    
    return extract_func(
        message=message,
        system_prompt=system_prompt,
        timeout=timeout,
        model=model
    )
