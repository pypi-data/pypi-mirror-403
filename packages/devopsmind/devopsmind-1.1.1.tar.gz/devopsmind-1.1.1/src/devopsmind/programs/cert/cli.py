from rich.panel import Panel
from rich.text import Text

from devopsmind.programs.cert.preview import open_or_preview_certificate


def program_cert_cli(args):
    """
    devopsmind program cert <program>
    """

    if not args or len(args) < 1:
        return Panel(
            Text(
                "Usage:\n\n"
                "  devopsmind program cert <program>\n",
                style="dim",
            ),
            title="Program Certificate",
        )

    program = args[0].lower()

    try:
        pdf, mode = open_or_preview_certificate(program)
    except Exception as e:
        return Panel(Text(str(e), style="red"))

    if mode == "final":
        body = Text(
            "🎓 Final certificate opened successfully.\n\n"
            f"{pdf}\n\n"
            "This certificate is final and verified.",
            style="green",
        )
        title = "Program Certificate"
    else:
        body = Text(
            "📄 Certificate preview generated.\n\n"
            f"{pdf}\n\n"
            "This is a preview only.\n"
            "Your program is NOT marked complete.\n\n"
            "When ready:\n"
            f"  devopsmind program submit {program}",
            style="green",
        )
        title = "Certificate Preview"

    return Panel(
        body,
        title=title,
        border_style="green",
    )
