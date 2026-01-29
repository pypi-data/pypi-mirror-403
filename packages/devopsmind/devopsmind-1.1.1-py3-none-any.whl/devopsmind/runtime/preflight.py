import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

RUNTIME_MARKER = Path.home() / ".devopsmind/runtime_pulled"
DEFAULT_IMAGE = "infraforgelabs/devopsmind-runtime:1.0"


def ensure_runtime_image(image: str | None = None):
    console = Console()
    image = image or DEFAULT_IMAGE

    # -------------------------------------------------
    # Already pulled
    # -------------------------------------------------
    if RUNTIME_MARKER.exists():
        return

    console.print(
        Panel(
            Text(
                "📦 Preparing DevOpsMind Runtime\n\n"
                "This is a one-time setup.\n"
                "The runtime image will be downloaded and reused.\n\n"
                "✔ Offline-safe after first pull\n"
                "✔ No system files modified\n"
                "✔ No cloud accounts required",
                justify="left",
            ),
            title="First-Run Setup",
            border_style="cyan",
        )
    )

    # -------------------------------------------------
    # Pull image with live output
    # -------------------------------------------------
    process = subprocess.Popen(
        ["docker", "pull", image],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    for line in process.stdout:
        console.print(line.rstrip())

    rc = process.wait()
    if rc != 0:
        raise RuntimeError("Docker image pull failed")

    RUNTIME_MARKER.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_MARKER.write_text("ok")

