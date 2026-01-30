#!/usr/bin/env python3
"""
AI message classifier supporting multiple providers

Classifies messages into categories: CALENDAR, TASK, MEMO
"""
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provider import classify_with_provider, PROVIDER_OPENROUTER

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a very responsible classifier. For every user message, output exactly one uppercase token and nothing else: CALENDAR, TASK, MEMO . Rules:
- CALENDAR: scheduling intent or an event/reminder with a date/time or scheduling words (e.g., "tomorrow", "at 3pm", "on Jan 5", "meeting", "appointment", "schedule", "remind me on"). If both scheduling and other intent appear, choose CALENDAR.
- TASK: actionable instruction or to‑do without specific scheduling (imperative verbs like "buy", "write", "call", "create", "finish", requests to add a task). If both task and memo appear, choose TASK.
- MEMO: factual note or something meant to be remembered (phrases like "remember that", "note", personal info to keep, facts).
- In the case the classification is ambiguous, inconclusive or impossible, prepend the notice "Unclear: MEMO" and clasify it as MEMO.

Tie-breakers: prefer CALENDAR over TASK over MEMO. Always return only the tag (no punctuation, no explanation).

Examples:
"Meeting with Alice tomorrow at 10am" -> CALENDAR
"Buy groceries" -> TASK
"Remember my passport number: 1234" -> MEMO
"What's the weather like?" -> MEMO
"Whatever. Test." -> MEMO (Unclear: MEMO)
"""


def classify_message(message_text, timeout=10, provider=PROVIDER_OPENROUTER):
    """
    Classify a message using the specified provider

    Args:
        message_text: The message content to classify
        timeout: API request timeout in seconds (default: 10)
        provider: Provider name ('openrouter' or 'ollama', default: 'openrouter')

    Returns:
        tuple: (success: bool, classification: str, raw_response: dict)
            - success: True if API call succeeded
            - classification: One of CALENDAR, TASK, MEMO or None on error
            - raw_response: Full API response dict or error dict
    """
    if not message_text or not message_text.strip():
        logger.warning("Empty message text provided for classification")
        return False, "MEMO", {"error": "Empty message"}

    success, classification, raw_response = classify_with_provider(
        provider=provider,
        message=message_text,
        system_prompt=SYSTEM_PROMPT,
        timeout=timeout
    )

    if success and classification:
        valid_classes = ['CALENDAR', 'TASK', 'MEMO']
        if classification not in valid_classes:
            logger.warning(f"Unexpected classification: {classification}, defaulting to MEMO")
            classification = 'MEMO'

    return success, classification, raw_response


def classify_message_simple(message_text, timeout=10, provider=PROVIDER_OPENROUTER):
    """
    Simplified classification function that returns just the classification

    Args:
        message_text: The message content to classify
        timeout: API request timeout in seconds (default: 10)
        provider: Provider name ('openrouter' or 'ollama', default: 'openrouter')

    Returns:
        str: Classification (CALENDAR, TASK, MEMO) or None on error
    """
    success, classification, _ = classify_message(message_text, timeout, provider)
    return classification if success else None
