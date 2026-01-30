#!/usr/bin/env python3
"""
Task extraction module for AI classifier

Handles task detection and extraction using OpenRouter API
"""
import os
import sys
import logging
from console import fg, fx
import datetime as dt
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provider import extract_with_provider, PROVIDER_OPENROUTER

logger = logging.getLogger(__name__)

TASK_EXTRACTION_PROMPT = """The following text was identified as a task/action item. Extract task name, due date (optional), priority, and details and call the tool add2task().

Current date and time: {current_datetime}

STRICT REQUIREMENTS:
- task_name: Clear, concise name/title for the task
- due_date: Due date in YYYY-MM-DD format. Use null if no due date is specified.
- priority: Priority level: "high", "medium", or "low"
- details: Additional context, notes, or description (can be empty string)

Return a JSON object with the following structure:
{{
    "task_name": "concise task name",
    "due_date": "YYYY-MM-DD format or null",
    "priority": "high | medium | low",
    "details": "additional context or empty string"
}}

Examples:
Input: "Buy groceries tomorrow"
Output: {{"task_name": "Buy groceries", "due_date": "2025-01-07", "priority": "medium", "details": ""}}

Input: "Finish report by Friday high priority"
Output: {{"task_name": "Finish report", "due_date": "2025-01-10", "priority": "high", "details": ""}}

Input: "Call mom"
Output: {{"task_name": "Call mom", "due_date": null, "priority": "low", "details": ""}}
""".format(current_datetime=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def update_task(task, task_name, due_date, priority, details):
    """
    Update task with proper values for Google Tasks API

    Args:
        task: Task dict to update
        task_name: Task title/name
        due_date: Due date in YYYY-MM-DD format or None
        priority: Priority level (high, medium, low)
        details: Additional details/notes

    Returns:
        dict: Updated task dict
    """
    task['title'] = task_name
    task['notes'] = details or ''

    if priority == 'high':
        task['status'] = 'needsAction'
        task['completed'] = None
    else:
        task['status'] = 'needsAction'

    if due_date:
        task['due'] = f"{due_date}T00:00:00Z"

    return task


def get_google_tasks_list_id(service, list_name="My Tasks"):
    """
    Get the task list ID for a specific list name

    Args:
        service: Google Tasks service
        list_name: Name of the task list to find

    Returns:
        str: Task list ID or '@default' if not found
    """
    try:
        results = service.tasklists().list().execute()
        lists = results.get('items', [])

        for tasklist in lists:
            if tasklist.get('title', '').lower() == list_name.lower():
                return tasklist.get('id')

        return '@default'
    except Exception as e:
        logger.warning(f"Failed to find task list '{list_name}': {e}")
        return '@default'


def add2task(task_name, due_date, priority, details, task_list_name="My Tasks"):
    """
    Add a task to Google Tasks

    Args:
        task_name: Name/title of the task
        due_date: Due date in YYYY-MM-DD format or None
        priority: Priority level (high, medium, low)
        details: Additional details or notes
        task_list_name: Name of the task list (default: "My Tasks")

    Returns:
        dict: Result of the task add operation
    """
    print(f"[add2task] Adding task: {task_name}")
    if due_date:
        print(f"[add2task] Due date: {due_date}")
    print(f"[add2task] Priority: {priority}")
    if details:
        print(f"[add2task] Details: {details}")

    task = {
        'title': 'PLACEHOLDER',
        'notes': '',
        'status': 'needsAction',
        'due': None,
    }

    task = update_task(task, task_name, due_date, priority, details)

    print(f"[add2task] Task constructed successfully!")
    print(f"[add2task] Task body: {task}")

    try:
        creds = None
        token_file = os.path.expanduser('~/.config/google/token.json')
        credentials_file = os.path.expanduser('~/.config/google/credentials.json')

        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(
                token_file,
                ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/tasks']
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print(f"[add2task] Refreshing expired credentials...")
                creds.refresh(Request())
            elif os.path.exists(credentials_file):
                print(f"[add2task] Running OAuth flow for Google Tasks...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file,
                    ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/tasks']
                )
                creds = flow.run_local_server(port=0)
            else:
                print(f"{fg.red}[add2task] Error: No Google credentials found.{fg.default}")
                print(f"{fg.yellow}Place OAuth credentials at: ~/.config/google/credentials.json{fg.default}")
                return {
                    "success": False,
                    "error": "No Google credentials found",
                    "task": task
                }

            os.makedirs(os.path.dirname(token_file), exist_ok=True)
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
            print(f"[add2task] Credentials saved to {token_file}")

        service = build('tasks', 'v1', credentials=creds)

        tasklist_id = get_google_tasks_list_id(service, task_list_name)
        print(f"[add2task] Using task list: {task_list_name} (ID: {tasklist_id})")

        inserted_task = service.tasks().insert(tasklist=tasklist_id, body=task).execute()

        print(f"{fg.green}[add2task] Task created successfully!{fg.default}")
        print(f"[add2task] Task ID: {inserted_task.get('id')}")

        return {
            "success": True,
            "task_name": task_name,
            "due_date": due_date,
            "priority": priority,
            "details": details,
            "task": task,
            "task_id": inserted_task.get('id')
        }

    except Exception as e:
        print(f"{fg.red}[add2task] Error inserting task: {e}{fg.default}")
        return {
            "success": False,
            "error": str(e),
            "task": task
        }


def extract_task_details(message_text, timeout=10, provider=PROVIDER_OPENROUTER):
    """
    Extract task details from a message using the specified provider

    Args:
        message_text: The task message to extract details from
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
        system_prompt=TASK_EXTRACTION_PROMPT,
        timeout=timeout
    )

    return success, details, raw_response
