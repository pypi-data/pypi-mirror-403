import subprocess
import shutil
import json
import urllib.request
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# -------------------------------------------------
# Constants
# -------------------------------------------------
VERSION_URL = (
    "https://raw.githubusercontent.com/"
    "InfraForgeLabs/infraforgelabs.github.io/main/meta/devopsmind/version.json"
)

RUNTIME_IMAGE_REPO = "infraforgelabs/devopsmind-runtime"
RUNTIME_MARKER = Path.home() / ".devopsmind" / "runtime_ready"
RUNTIME_VERSION_FILE = Path.home() / ".devopsmind" / "runtime_version"

console = Console()

# -------------------------------------------------
# Docker helpers
# -------------------------------------------------
def _docker_available() -> bool:
    return shutil.which("docker") is not None


def _docker_usable() -> bool:
    try:
        subprocess.run(
            ["docker", "ps"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except Exception:
        return False


def _image_exists(image: str) -> bool:
    return (
        subprocess.run(
            ["docker", "image", "inspect", image],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


# -------------------------------------------------
# Runtime version helpers (RUNTIME ONLY)
# -------------------------------------------------
def _fetch_runtime_version() -> str:
    with urllib.request.urlopen(VERSION_URL, timeout=5) as resp:
        data = json.load(resp)

    if "runtime_version" not in data:
        raise RuntimeError("runtime_version not found in version metadata")

    return str(data["runtime_version"]).strip()


def _local_runtime_version() -> str | None:
    if not RUNTIME_VERSION_FILE.exists():
        return None
    return RUNTIME_VERSION_FILE.read_text().strip()


def _write_runtime_version(version: str):
    RUNTIME_VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_VERSION_FILE.write_text(version)


# -------------------------------------------------
# Runtime operations (IMAGE ONLY)
# -------------------------------------------------
def _pull_runtime_image(image: str):
    console.print(
        Panel(
            Text(
                "Preparing DevOpsMind runtime image.\n\n"
                "✔ Checking runtime version\n"
                "✔ Pulling required image\n"
                "✔ Fully offline after this\n",
                justify="left",
            ),
            title="DevOpsMind Runtime",
            border_style="cyan",
        )
    )

    result = subprocess.run(
        ["docker", "pull", image],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if result.returncode != 0:
        raise RuntimeError("Failed to pull DevOpsMind runtime image")


# -------------------------------------------------
# Public entrypoint
# -------------------------------------------------
def handle_init():
    console.clear()

    console.print(
        Panel(
            Text(
                "DevOpsMind uses a shared runtime IMAGE.\n\n"
                "✔ Pulled once\n"
                "✔ Used to create per-lab containers\n"
                "✔ No long-running containers\n"
                "✔ Fully offline after init\n",
                justify="left",
            ),
            title="DevOpsMind Setup",
            border_style="blue",
        )
    )

    if not _docker_available():
        console.print(
            Panel(
                Text("Docker is required but not available.", style="red"),
                title="Docker Not Available",
                border_style="red",
            )
        )
        return

    if not _docker_usable():
        console.print(
            Panel(
                Text(
                    "Docker is installed but not accessible.\n\n"
                    "Run:\n  sudo usermod -aG docker $USER\n  newgrp docker",
                    style="red",
                ),
                title="Docker Permission Issue",
                border_style="red",
            )
        )
        return

    try:
        required_runtime_version = _fetch_runtime_version()
    except Exception:
        console.print(
            Panel(
                Text("Unable to check runtime version.", style="red"),
                title="Runtime Version Check Failed",
                border_style="red",
            )
        )
        return

    runtime_image = f"{RUNTIME_IMAGE_REPO}:{required_runtime_version}"
    image_exists = _image_exists(runtime_image)
    local_runtime_version = _local_runtime_version()

    is_first_install = not image_exists
    runtime_needs_update = (
        image_exists and local_runtime_version != required_runtime_version
    )

    if is_first_install:
        console.print(
            Panel(
                Text(
                    f"Runtime image not found.\n\n"
                    f"✔ Required runtime version: {required_runtime_version}",
                    justify="left",
                ),
                title="Runtime Setup",
                border_style="cyan",
            )
        )

    elif runtime_needs_update:
        console.print(
            Panel(
                Text(
                    f"Runtime image update required.\n\n"
                    f"✔ Required runtime version: {required_runtime_version}",
                    justify="left",
                ),
                title="Runtime Update",
                border_style="cyan",
            )
        )

    if is_first_install or runtime_needs_update:
        try:
            _pull_runtime_image(runtime_image)
        except Exception as e:
            console.print(
                Panel(Text(str(e), style="red"), title="Runtime Update Failed")
            )
            return

        _write_runtime_version(required_runtime_version)
        status = "Runtime image ready"

    else:
        status = "DevOpsMind runtime image already up to date"

    RUNTIME_MARKER.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_MARKER.write_text("ok")

    console.print(
        Panel(
            Text(
                f"✔ {status}\n"
                f"✔ Runtime version: {required_runtime_version}\n"
                "✔ Ready to start labs\n\n"
                "Happy Learning ❤️",
                style="green",
            ),
            title="Runtime Ready",
            border_style="green",
        )
    )
