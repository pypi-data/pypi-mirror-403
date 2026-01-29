# src/devopsmind/programs/ui.py

from rich.console import Group
from rich.text import Text

from devopsmind.cli.cli import frame


def boxed_program(title: str, body):
    """
    Program-scoped boxed layout.

    - NO global profile/status bar
    - Used ONLY for program commands
    - Keeps visual consistency with main UI
    """
    items = [
        body,
    ]
    return frame(title, Group(*items))
