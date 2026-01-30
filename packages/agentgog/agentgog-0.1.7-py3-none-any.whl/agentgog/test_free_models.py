#!/usr/bin/env python3
"""
Test all free OpenRouter models with a simple prompt
Record results including error codes and responses
"""
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from openrouter_client import get_api_key, chat_with_openrouter

logger = logging.getLogger(__name__)


def fetch_free_models() -> List[Dict[str, Any]]:
    """
    Fetch all free models from OpenRouter

    Returns:
        List of free model dictionaries
    """
    import requests

    api_key = get_api_key()

    if not api_key:
        logger.error("No API key found")
        return []

    url = "https://openrouter.ai/api/v1/models/user"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        all_models = data.get("data", [])

        free_models = []
        for model in all_models:
            pricing = model.get("pricing", {})
            if pricing.get("prompt") == "0" and pricing.get("completion") == "0":
                free_models.append(model)

        return free_models

    except Exception as e:
        logger.error(f"Failed to fetch models: {e}")
        return []


def test_model(model_id: str, prompt: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Test a single model with a prompt

    Args:
        model_id: Model ID to test
        prompt: Test prompt
        timeout: Request timeout

    Returns:
        Dictionary with test results
    """
    result = {
        "model_id": model_id,
        "status": "unknown",
        "error_code": None,
        "error_message": None,
        "response": None,
        "response_length": None,
        "latency_ms": None
    }

    start_time = time.time()

    try:
        success, content, raw_response = chat_with_openrouter(
            message=prompt,
            timeout=timeout,
            model=model_id
        )

        latency = (time.time() - start_time) * 1000
        result["latency_ms"] = round(latency, 2)

        if success and content:
            result["status"] = "success"
            result["response"] = content
            result["response_length"] = len(content)
        else:
            result["status"] = "failed"
            if isinstance(raw_response, dict):
                error_info = raw_response.get("error", {})
                if isinstance(error_info, dict):
                    result["error_code"] = error_info.get("code")
                    result["error_message"] = error_info.get("message")
                elif isinstance(error_info, str):
                    if "Error:" in error_info:
                        parts = error_info.split("Error:", 1)
                        result["error_code"] = parts[0].strip()
                        result["error_message"] = parts[1].strip()
                    else:
                        result["error_message"] = error_info
            else:
                result["error_message"] = str(raw_response)

    except Exception as e:
        latency = (time.time() - start_time) * 1000
        result["latency_ms"] = round(latency, 2)
        result["status"] = "exception"
        result["error_message"] = str(e)

    return result


def run_model_tests(
    test_prompt: str = "Who are you?",
    timeout: int = 10,
    delay_between_requests: float = 1.0,
    output_file: str = None
) -> List[Dict[str, Any]]:
    """
    Run tests on all free models

    Args:
        test_prompt: Prompt to test with
        timeout: Request timeout per model
        delay_between_requests: Delay in seconds between requests
        output_file: JSON file to save results (default: auto-generated)

    Returns:
        List of test results
    """
    logger.info(f"Testing all free models with prompt: '{test_prompt}'")

    free_models = fetch_free_models()

    if not free_models:
        logger.error("No free models found")
        return []

    logger.info(f"Found {len(free_models)} free models to test")

    results = []

    for i, model in enumerate(free_models, 1):
        model_id = model.get("id", "unknown")
        logger.info(f"Testing {i}/{len(free_models)}: {model_id}")

        result = test_model(model_id, test_prompt, timeout)
        results.append(result)

        if delay_between_requests > 0:
            time.sleep(delay_between_requests)

    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"model_test_results_{timestamp}.json"

    output_path = Path(output_file)

    try:
        output_path.write_text(
            json.dumps({
                "timestamp": datetime.now().isoformat(),
                "test_prompt": test_prompt,
                "total_models": len(free_models),
                "results": results
            }, indent=2),
            encoding="utf-8"
        )
        logger.info(f"Results saved to {output_path}")

    except Exception as e:
        logger.error(f"Failed to save results: {e}")

    return results


def print_summary(results: List[Dict[str, Any]]):
    """
    Print a summary of test results

    Args:
        results: List of test results
    """
    if not results:
        print("No results to display")
        return

    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] in ("failed", "exception")]

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total models tested: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if successful:
        print(f"\nSuccessful models ({len(successful)}):")
        for r in successful:
            print(f"  ✓ {r['model_id']} ({r['response_length']} chars, {r['latency_ms']}ms)")

    if failed:
        print(f"\nFailed models ({len(failed)}):")
        for r in failed:
            error = r.get("error_code") or r.get("error_message") or "Unknown error"
            print(f"  ✗ {r['model_id']} - {error}")

    print("=" * 80)

    error_codes = {}
    for r in failed:
        code = r.get("error_code") or "other"
        error_codes[code] = error_codes.get(code, 0) + 1

    if error_codes:
        print("\nError distribution:")
        for code, count in sorted(error_codes.items(), key=lambda x: str(x[0])):
            print(f"  {code}: {count}")


def main():
    """
    Main function
    """
    logging.basicConfig(level=logging.INFO)

    results = run_model_tests(
        test_prompt="Who are you?",
        timeout=15,
        delay_between_requests=0.5
    )

    print_summary(results)


if __name__ == "__main__":
    main()
