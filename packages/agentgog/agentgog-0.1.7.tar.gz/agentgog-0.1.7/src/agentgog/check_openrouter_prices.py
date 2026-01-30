#!/usr/bin/env python3
"""
Check OpenRouter model prices and print free models
"""
import requests
import json
import os
import logging

from openrouter_client import get_api_key

logger = logging.getLogger(__name__)

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models/user"


def fetch_models():
    """
    Fetch available models from OpenRouter API

    Returns:
        tuple: (success: bool, models: list or None, error: str or None)
    """
    api_key = get_api_key()

    if not api_key:
        logger.error("OPENROUTER_API_KEY environment variable not set and ~/.openai_openrouter.key not found")
        return False, None, "Missing API key"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        logger.info("Fetching models from OpenRouter API...")
        response = requests.get(OPENROUTER_MODELS_URL, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        models = data.get("data", [])

        logger.info(f"Successfully fetched {len(models)} models")
        return True, models, None

    except requests.exceptions.Timeout:
        logger.error("OpenRouter API request timed out")
        return False, None, "Timeout"

    except requests.exceptions.RequestException as e:
        logger.error(f"OpenRouter API request failed: {e}")
        return False, None, str(e)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse API response: {e}")
        return False, None, f"JSON decode error: {e}"

    except Exception as e:
        logger.error(f"Unexpected error fetching models: {e}", exc_info=True)
        return False, None, str(e)


def filter_free_models(models):
    """
    Filter models that are free (pricing is 0)

    Args:
        models: List of model dictionaries

    Returns:
        list: Free model dictionaries
    """
    free_models = []

    for model in models:
        pricing = model.get("pricing", {})
        prompt_price = pricing.get("prompt", "0")
        completion_price = pricing.get("completion", "0")

        if prompt_price == "0" and completion_price == "0":
            free_models.append(model)

    return free_models


def extract_model_size(model_id):
    """
    Extract model size from model ID string

    Args:
        model_id: Model ID string (e.g., "openai/gpt-4-30b:free")

    Returns:
        int: Model size in billions, or 0 if not found
    """
    import re

    pattern = r'-e?(\d+)b[:\-]'
    match = re.search(pattern, model_id.lower())

    if match:
        return int(match.group(1))

    return 0


def print_free_models(free_models):
    """
    Print free models in a readable format, sorted by model size (descending)

    Args:
        free_models: List of free model dictionaries
    """
    if not free_models:
        print("No free models found")
        return

    sorted_models = sorted(free_models, key=lambda m: extract_model_size(m.get('id', '')), reverse=True)

    print(f"\nFound {len(sorted_models)} free models (sorted by model size):\n")
    print("-" * 80)

    for i, model in enumerate(sorted_models, 1):
        model_id = model.get('id', 'Unknown')
        size = extract_model_size(model_id)
        size_str = f"{size}B" if size > 0 else "Unknown"

        print(f"\n{i}. ID: {model_id}")
        print(f"   Size/Context: {size_str}/{model.get('context_length', 'Unknown')}")
        print(f"   Description: {model.get('description', 'No description')[:100]}")

    print("\n" + "-" * 80)


def main():
    """
    Main function to fetch and display free models
    """
    logging.basicConfig(level=logging.INFO)

    success, models, error = fetch_models()

    if not success:
        print(f"Error: {error}")
        return

    free_models = filter_free_models(models)
    print_free_models(free_models)

    print(f"\nTotal models: {len(models)}")
    print(f"Free models: {len(free_models)}")


if __name__ == "__main__":
    main()
