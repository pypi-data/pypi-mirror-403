"""Shell Approval plugin - Asks user approval for shell commands."""

import re
from typing import TYPE_CHECKING
from connectonion.core.events import before_each_tool

if TYPE_CHECKING:
    from connectonion.core.agent import Agent

SAFE_PATTERNS = [
    r'^ls\b', r'^ll\b', r'^cat\b', r'^head\b', r'^tail\b', r'^less\b', r'^more\b',
    r'^grep\b', r'^rg\b', r'^find\b', r'^fd\b', r'^which\b', r'^whereis\b',
    r'^type\b', r'^file\b', r'^stat\b', r'^wc\b', r'^pwd\b', r'^echo\b',
    r'^printf\b', r'^date\b', r'^whoami\b', r'^id\b', r'^env\b', r'^printenv\b',
    r'^uname\b', r'^hostname\b', r'^df\b', r'^du\b', r'^free\b', r'^ps\b',
    r'^top\b', r'^htop\b', r'^tree\b',
    r'^git\s+status\b', r'^git\s+log\b', r'^git\s+diff\b', r'^git\s+show\b',
    r'^git\s+branch\b', r'^git\s+remote\b', r'^git\s+tag\b',
    r'^npm\s+list\b', r'^npm\s+ls\b', r'^pip\s+list\b', r'^pip\s+show\b',
    r'^python\s+--version\b', r'^node\s+--version\b', r'^cargo\s+--version\b',
]


def _is_safe(command: str) -> bool:
    cmd = command.strip()
    return any(re.search(pattern, cmd) for pattern in SAFE_PATTERNS)


def _check_approval(agent: 'Agent') -> None:
    pending = agent.current_session.get('pending_tool') if agent.current_session else None
    if not pending:
        return

    tool_name = pending.get('name', '')
    if tool_name not in ('bash', 'shell', 'run', 'run_in_dir'):
        return

    args = pending.get('arguments', {})
    command = args.get('command', '')
    base_cmd = command.strip().split()[0] if command.strip() else ''

    approved_cmds = agent.current_session.get('shell_approved_cmds', set()) if agent.current_session else set()
    if base_cmd in approved_cmds:
        return

    if _is_safe(command):
        return

    from connectonion.cli.co_ai.tui.context import is_tui_active, show_choice_selector_sync, show_modal_sync
    
    if is_tui_active():
        from connectonion.cli.co_ai.tui.modals import TextInputModal
        
        truncated = command[:60] + "..." if len(command) > 60 else command
        question = f"Execute: `{truncated}`"
        options = [
            "Yes, execute",
            f"Auto approve '{base_cmd}' for this session",
            "No, tell agent what I want",
        ]
        
        choice = show_choice_selector_sync(question, options, allow_other=False)
        
        if choice == options[0]:
            return
        elif choice == options[1]:
            if agent.current_session is not None:
                if 'shell_approved_cmds' not in agent.current_session:
                    agent.current_session['shell_approved_cmds'] = set()
                agent.current_session['shell_approved_cmds'].add(base_cmd)
            return
        else:
            feedback = show_modal_sync(TextInputModal("What do you want instead?"))
            raise ValueError(f"User feedback: {feedback}")
    else:
        from rich.console import Console
        from rich.panel import Panel
        from rich.syntax import Syntax
        from connectonion.tui import pick
        
        console = Console()
        console.print()
        syntax = Syntax(command, "bash", theme="monokai", word_wrap=True)
        console.print(Panel(syntax, title="[yellow]Shell Command[/yellow]", border_style="yellow"))
        
        choice = pick("Execute this command?", [
            "Yes, execute",
            f"Auto approve '{base_cmd}' in this session",
            "No, tell agent what I want"
        ], console=console)
        
        if choice == "Yes, execute":
            return
        elif choice.startswith("Auto approve"):
            if agent.current_session is not None:
                if 'shell_approved_cmds' not in agent.current_session:
                    agent.current_session['shell_approved_cmds'] = set()
                agent.current_session['shell_approved_cmds'].add(base_cmd)
            return
        else:
            feedback = input("What do you want the agent to do instead? ")
            raise ValueError(f"User feedback: {feedback}")


shell_approval = [before_each_tool(_check_approval)]
