from rich.text import Text

def show_secret_reveal(secret_achievements):
    if not secret_achievements:
        return None

    return Text(
        "🟣 Something rare was unlocked.",
        style="dim magenta",
    )
