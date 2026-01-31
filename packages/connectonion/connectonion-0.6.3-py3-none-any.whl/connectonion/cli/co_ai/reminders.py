"""System reminders for contextual guidance.

System reminders are automatically injected into tool results or conversation
to provide contextual constraints and guidance. They override default behavior
when applicable.

Usage:
    from connectonion.cli.co_ai.reminders import inject_reminder, REMINDERS

    # Inject a specific reminder
    result = inject_reminder(tool_result, "plan_mode_active")

    # Check if reminder should be shown
    if should_show_todo_reminder(agent):
        result = inject_reminder(result, "todo_reminder")
"""

from typing import Optional, Dict, Any
from functools import wraps


# System reminder templates
REMINDERS: Dict[str, str] = {
    # Plan mode reminder - injected when plan mode is active
    "plan_mode_active": """<system-reminder>
Plan mode is active. You are in READ-ONLY exploration mode.
- You can ONLY use: glob, grep, read_file to explore
- You can ONLY write to the plan file (.co/PLAN.md)
- Do NOT make any code changes until plan is approved
- Use write_plan() to update your plan
- Use exit_plan_mode() when plan is complete
</system-reminder>""",

    # Todo reminder - gentle nudge to use todo tracking
    "todo_reminder": """<system-reminder>
Consider using todo_list() to track progress for multi-step tasks.
Mark tasks complete immediately when finished.
</system-reminder>""",

    # Read-only mode for explore agent
    "read_only": """<system-reminder>
This is READ-ONLY mode. You are PROHIBITED from modifying any files.
Only use: glob, grep, read_file, and read-only bash commands.
</system-reminder>""",

    # Security reminder after reading sensitive files
    "security": """<system-reminder>
This file may contain sensitive information (credentials, keys, tokens).
- Never expose secrets in output
- Never commit this file if it contains real credentials
- Consider using environment variables instead
</system-reminder>""",

    # Anti-over-engineering reminder
    "simplicity": """<system-reminder>
Keep it simple:
- Only change what's directly needed
- Don't add error handling for scenarios that can't happen
- Three similar lines > premature abstraction
- If unused, delete completely
</system-reminder>""",

    # Workflow reminder - injected when writing Python files
    "connectonion_workflow": """<system-reminder>
When creating agents, ALWAYS use ConnectOnion framework:
- `from connectonion import Agent`
- Atomic tool functions (one thing each)
- `agent = Agent("name", tools=[...])` + `agent.input("task")`

NEVER create standalone scripts with argparse. NEVER skip ask_user confirmation.
</system-reminder>""",

    # After code write reminder
    "after_write_code": """<system-reminder>
Code written. If this is an agent:
- Verify it uses `from connectonion import Agent`
- Verify tools are atomic functions
- If it's a standalone script with argparse, REWRITE using ConnectOnion
</system-reminder>""",
}


def inject_reminder(content: str, reminder_key: str) -> str:
    """
    Inject a system reminder into content.

    Args:
        content: The original content (tool result, message, etc.)
        reminder_key: Key from REMINDERS dict

    Returns:
        Content with reminder injected at the end
    """
    if reminder_key not in REMINDERS:
        return content

    reminder = REMINDERS[reminder_key]
    return f"{content}\n\n{reminder}"


def with_reminder(reminder_key: str):
    """
    Decorator to inject a reminder into tool results.

    Usage:
        @with_reminder("plan_mode_active")
        def some_tool(...):
            return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if isinstance(result, str):
                return inject_reminder(result, reminder_key)
            return result
        return wrapper
    return decorator


def should_show_security_reminder(file_path: str) -> bool:
    """Check if file path suggests sensitive content."""
    sensitive_patterns = [
        ".env",
        "credentials",
        "secrets",
        "config/prod",
        "keys",
        "password",
        "token",
        ".pem",
        ".key",
    ]
    path_lower = file_path.lower()
    return any(pattern in path_lower for pattern in sensitive_patterns)


def get_contextual_reminders(context: Dict[str, Any]) -> list:
    """
    Get list of reminders based on current context.

    Args:
        context: Dict with current state info:
            - plan_mode: bool
            - todo_count: int
            - file_path: str (for security check)

    Returns:
        List of reminder keys that should be shown
    """
    reminders = []

    if context.get("plan_mode"):
        reminders.append("plan_mode_active")

    if context.get("file_path") and should_show_security_reminder(context["file_path"]):
        reminders.append("security")

    return reminders
