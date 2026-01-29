from pathlib import Path
import json
import subprocess
import urllib.request

from rich.console import Console
from rich.text import Text

from devopsmind.handlers.ui_helpers import boxed
from devopsmind.safety.safe_shell import launch_safe_shell
from devopsmind.handlers.lab_utils import load_lab_metadata
from devopsmind.list.lab_resolver import find_lab_by_id
from devopsmind.runtime.lab_container import (
    start_lab_container,
    generate_session_id,
)

console = Console()

# -------------------------------------------------
# Constants
# -------------------------------------------------
WORKSPACE_DIR = Path.home() / "workspace"
RUNTIME_MARKER = Path.home() / ".devopsmind" / "runtime_ready"
RUNTIME_VERSION_FILE = Path.home() / ".devopsmind" / "runtime_version"

VERSION_URL = (
    "https://raw.githubusercontent.com/"
    "InfraForgeLabs/infraforgelabs.github.io/main/meta/devopsmind/version.json"
)

# -------------------------------------------------
# Runtime helpers (same rules as start)
# -------------------------------------------------
def _fetch_required_runtime_version() -> str | None:
    try:
        with urllib.request.urlopen(VERSION_URL, timeout=5) as resp:
            data = json.load(resp)
        return str(data.get("runtime_version")).strip()
    except Exception:
        return None


def _local_runtime_version() -> str | None:
    if not RUNTIME_VERSION_FILE.exists():
        return None
    return RUNTIME_VERSION_FILE.read_text().strip()


def _runtime_image_exists(version: str) -> bool:
    image = f"infraforgelabs/devopsmind-runtime:{version}"
    return (
        subprocess.run(
            ["docker", "image", "inspect", image],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


# -------------------------------------------------
# 🚀 PUBLIC ENTRYPOINT
# -------------------------------------------------
def handle_resume(args, console: Console = console):
    console.clear()

    lab_id = getattr(args, "id", None)

    # -------------------------------------------------
    # 🔒 Runtime pre-checks (IMAGE-BASED, NOT CONTAINER)
    # -------------------------------------------------
    if not RUNTIME_MARKER.exists():
        console.print(
            boxed(
                "❌ Runtime Not Initialized",
                Text(
                    "DevOpsMind runtime has not been initialized.\n\n"
                    "Run:\n\n"
                    "  devopsmind init",
                    style="red",
                ),
            )
        )
        return

    required = _fetch_required_runtime_version()
    local = _local_runtime_version()

    if not required or local != required or not _runtime_image_exists(required):
        console.print(
            boxed(
                "⚠ Runtime Update Required",
                Text(
                    "Your DevOpsMind runtime is outdated.\n\n"
                    f"Installed version : {local or 'not installed'}\n"
                    f"Required version  : {required or 'unknown'}\n\n"
                    "Run:\n\n"
                    "  devopsmind init",
                    style="yellow",
                ),
            )
        )
        return

    # -------------------------------------------------
    # 📂 No ID → list resumable workspaces (IDS ONLY)
    # -------------------------------------------------
    if not lab_id:
        if not WORKSPACE_DIR.exists():
            console.print(
                boxed(
                    "▶ Resume",
                    Text("No resumable labs found."),
                )
            )
            return

        workspaces = sorted(
            p.name for p in WORKSPACE_DIR.iterdir() if p.is_dir()
        )

        if not workspaces:
            console.print(
                boxed(
                    "▶ Resume",
                    Text("No resumable labs found."),
                )
            )
            return

        console.print(
            boxed(
                "▶ Resume · Available Workspaces",
                Text(
                    "\n".join(workspaces)
                    + "\n\nUse:\n  devopsmind resume <lab-id>"
                ),
            )
        )
        return

    # -------------------------------------------------
    # 📂 Workspace check (NON-DESTRUCTIVE)
    # -------------------------------------------------
    workspace = WORKSPACE_DIR / lab_id
    if not workspace.exists():
        console.print(
            boxed(
                "❌ Nothing to Resume",
                Text(
                    f"No existing workspace found for '{lab_id}'.\n\n"
                    "Use:\n"
                    "  devopsmind start <id>",
                    style="red",
                ),
            )
        )
        return

    # -------------------------------------------------
    # 🔎 Locate lab source
    # -------------------------------------------------
    source = find_lab_by_id(lab_id)
    if not source:
        console.print(
            boxed(
                "❌ Resume Failed",
                Text(f"Lab '{lab_id}' not found.", style="red"),
            )
        )
        return

    data = load_lab_metadata(source)
    lab_title = data.get("title", lab_id)

    # -------------------------------------------------
    # 🚀 Start fresh per-lab container
    # -------------------------------------------------
    session_id = generate_session_id()

    container_name = start_lab_container(
        lab_id=lab_id,
        workspace=workspace,
        lab_source=source,
        session_id=session_id,
    )

    # -------------------------------------------------
    # UI (SECTIONED, LABELED)
    # -------------------------------------------------
    console.print(
        boxed(
            f"▶ Resume · {lab_id}",
            Text(
                f"Title: {lab_title}\n\n"
                "📂 Workspace:\n"
                f"~/workspace/{lab_id}\n\n"
                "Resuming existing DevOpsMind workspace.\n\n"
                "✔ Workspace preserved\n"
                "✔ Fresh isolated environment\n\n"
                "🔒 Entering DevOpsMind Safe Shell…",
            ),
        )
    )

    # -------------------------------------------------
    # 🔒 Safe Shell
    # -------------------------------------------------
    launch_safe_shell(
        workspace=workspace,
        lab_id=lab_id,
        stack=data.get("stack"),
        session_id=session_id,
        container_name=container_name,
        safety_overrides=data.get("safety", {}) or {},
    )
