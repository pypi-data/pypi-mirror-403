#!/usr/bin/env python3
"""
Memo extraction module for AI classifier

Handles memo detection and extraction using OpenRouter API
Stores memos in Simplenote
"""
import os
import sys
import logging
from console import fg, fx
import datetime as dt
import simplenote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provider import extract_with_provider, PROVIDER_OPENROUTER

logger = logging.getLogger(__name__)

MEMO_EXTRACTION_PROMPT = """The following text was identified as a memo/note to remember. Extract a concise title, the main content, and any labels/tags, then call the tool add2keep().

Current date and time: {current_datetime}

STRICT REQUIREMENTS:
- title: Short, descriptive title for the memo (max 50 characters)
- content: Main content/details to remember (MUST be  the original text)
- labels: List of labels/tags for categorization (can be empty list). Allowed labels: ['home', 'administration', 'important', 'web']

Return a JSON object with the following structure:
{{
    "title": "concise memo title (max 50 chars)",
    "content": "main content or details to remember",
    "labels": ["label1", "label2"] or []
}}

Examples:
Input: "Remember that my passport number is 123456789"
Output: {{"title": "Passport number", "content": "Passport number is 123456789", "labels": ["important"]}}

Input: "Mom's birthday is on December 15th"
Output: {{"title": "Mom's birthday", "content": "December 15th", "labels": ["home"]}}

Input: "Remember: there are 2 QR codes on Alianz document"
Output: {{"title": "Alianz document", "content": "there are 2 QR codes on Alianz document", "labels": ['administration']}}

Input: "The WiFi password is: Guest1234"
Output: {{"title": "WiFi password", "content": "Guest1234", "labels": ["web"]}}
""".format(current_datetime=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def get_simplenote_client():
    """
    Get Simplenote client with credentials from environment

    Returns:
        simplenote.Simplenote or None
    """
    user = os.environ.get('SIMPLENOTE_LOCAL_USER')
    password = os.environ.get('SIMPLENOTE_LOCAL_PASSWORD')

    if not user or not password:
        print(f"{fg.red}[add2keep] Error: SIMPLENOTE_LOCAL_USER and SIMPLENOTE_LOCAL_PASSWORD not set{fg.default}")
        print(f"{fg.yellow}Run: export SIMPLENOTE_LOCAL_USER=user@example.com{fg.default}")
        print(f"{fg.yellow}      export SIMPLENOTE_LOCAL_PASSWORD=yourpassword{fg.default}")
        return None

    try:
        return simplenote.Simplenote(user, password)
    except Exception as e:
        print(f"{fg.red}[add2keep] Error creating Simplenote client: {e}{fg.default}")
        return None


def add2keep(title, content, labels=None):
    """
    Add a memo to Simplenote

    Args:
        title: Title of the memo
        content: Main content/details to remember
        labels: List of labels/tags (default: empty list)

    Returns:
        dict: Result of the memo add operation
    """
    print(f"[add2keep] Adding memo: {title}")
    if labels:
        print(f"[add2keep] Labels: {labels}")

    note_content = f"{title}\n\n{content}\n\n*{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

    sn = get_simplenote_client()
    if not sn:
        return {
            "success": False,
            "error": "Simplenote credentials not configured",
            "title": title,
            "content": content,
            "labels": labels or []
        }

    try:
        note = {
            'content': note_content
        }

        if labels:
            note['tags'] = labels

        result = sn.add_note(note)

        if isinstance(result, tuple):
            note_data, status = result
        else:
            note_data = result

        print(f"{fg.green}[add2keep] Memo saved successfully!{fg.default}")
        print(f"[add2keep] Note key: {note_data.get('key', 'unknown')}")

        return {
            "success": True,
            "title": title,
            "content": content,
            "labels": labels or [],
            "note_key": note_data.get('key'),
            "note": note_data
        }

    except Exception as e:
        print(f"{fg.red}[add2keep] Error saving to Simplenote: {e}{fg.default}")
        return {
            "success": False,
            "error": str(e),
            "title": title,
            "content": content,
            "labels": labels or []
        }


def extract_memo_details(message_text, timeout=10, provider=PROVIDER_OPENROUTER):
    """
    Extract memo details from a message using the specified provider

    Args:
        message_text: The memo message to extract details from
        timeout: API request timeout in seconds (default: 10)
        provider: Provider name ('openrouter' or 'ollama', default: 'openrouter')

    Returns:
        tuple: (success: bool, details: dict or None, raw_response: dict)
    """
    if not message_text or not message_text.strip():
        logger.warning("Empty message text provided for extraction")
        return False, None, {"error": "Empty message"}

    success, details, raw_response = extract_with_provider(
        provider=provider,
        message=message_text,
        system_prompt=MEMO_EXTRACTION_PROMPT,
        timeout=timeout
    )

    return success, details, raw_response
