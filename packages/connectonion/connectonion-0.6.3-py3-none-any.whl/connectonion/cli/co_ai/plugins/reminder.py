"""
Reminder plugin - injects contextual reminders into tool results.

Like Claude Code's system reminders, these are appended to tool results
(not separate messages) to guide agent behavior without extra API calls.

Usage:
    from connectonion.cli.co_ai.plugins.reminder import reminder_plugin

    agent = Agent("coder", plugins=[reminder_plugin])
"""

from connectonion.core.events import after_each_tool
from ..reminders import REMINDERS, should_show_security_reminder


def _get_reminder_for_tool(tool_name: str, args: dict, result: str) -> str | None:
    """Determine which reminder to inject based on tool and context."""

    # write_file with .py extension → remind about ConnectOnion pattern
    if tool_name == "write_file":
        path = args.get("path", "") or args.get("file_path", "")
        if path.endswith(".py"):
            return "connectonion_workflow"

    # read_file with sensitive path → security reminder
    if tool_name in ("read_file", "read"):
        path = args.get("path", "") or args.get("file_path", "")
        if should_show_security_reminder(path):
            return "security"

    # bash/shell commands that modify code
    if tool_name in ("bash", "shell", "run_command"):
        cmd = args.get("command", "") or args.get("cmd", "")
        # If creating/editing Python files
        if any(x in cmd for x in [">.py", ">> .py", "cat >", "echo >", "sed -i"]):
            return "connectonion_workflow"

    return None


def inject_reminder_handler(agent):
    """Inject contextual reminders into tool results.

    This handler runs after each tool execution and modifies the
    tool result message to include relevant reminders.
    """
    trace = agent.current_session.get('trace', [])
    messages = agent.current_session.get('messages', [])

    if not trace or not messages:
        return

    # Get the most recent tool execution
    last_trace = trace[-1]
    if last_trace.get('type') != 'tool_result':
        return

    tool_name = last_trace.get('name', '')
    tool_args = last_trace.get('args', {})
    result = last_trace.get('result', '')

    # Determine which reminder to inject
    reminder_key = _get_reminder_for_tool(tool_name, tool_args, result)
    if not reminder_key or reminder_key not in REMINDERS:
        return

    # Find and modify the last tool result message
    for msg in reversed(messages):
        if msg.get('role') == 'tool':
            msg['content'] = msg.get('content', '') + '\n\n' + REMINDERS[reminder_key]
            break


# Export the plugin
reminder_plugin = [after_each_tool(inject_reminder_handler)]
