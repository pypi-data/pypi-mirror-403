# src/devopsmind/handlers/search/level_handler.py

from devopsmind.handlers.search.difficulty import VALID_DIFFICULTIES


def extract_level_filter(flags, console=None):
    """
    Extract and validate --level <Difficulty>.
    Applies ONLY to search.
    """

    if "--level" not in flags:
        return None

    try:
        idx = flags.index("--level")
        level = flags[idx + 1].capitalize()
    except (ValueError, IndexError):
        if console:
            console.print("[red]--level requires a value[/red]")
        return None

    if level not in VALID_DIFFICULTIES:
        if console:
            console.print(
                f"[red]Invalid level '{level}'. "
                f"Valid levels: {', '.join(sorted(VALID_DIFFICULTIES))}[/red]"
            )
        return None

    return level
