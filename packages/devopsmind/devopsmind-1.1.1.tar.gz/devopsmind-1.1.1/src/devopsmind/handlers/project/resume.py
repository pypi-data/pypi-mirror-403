"""
devopsmind project resume <project_id>

LOCKED BEHAVIOR:
- Explicit resume command
- Requires existing workspace
- Does NOT overwrite files
- Does NOT change state
- Reattaches runtime + safe project shell
"""

from pathlib import Path
import json
import time
import subprocess
import urllib.request
import yaml

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from devopsmind.handlers.id_normalizer import canonical_id
from devopsmind.handlers.project.describe import _available_project_ids
from devopsmind.handlers.ui_helpers import boxed
from devopsmind.state import load_state

from devopsmind.runtime.project_container import start_project_container
from devopsmind.safety.safe_project_shell import launch_safe_project_shell

console = Console()

# -------------------------------------------------
# Paths
# -------------------------------------------------
DEVOPSMIND_ROOT = Path(__file__).resolve().parents[2]
LABS_DIR = DEVOPSMIND_ROOT / "labs"

# 🔒 FIXED workspace location
WORKSPACE_ROOT = Path.home() / "workspace" / "project"

RUNTIME_VERSION_FILE = Path.home() / ".devopsmind" / "runtime_version"

VERSION_URL = (
    "https://raw.githubusercontent.com/"
    "InfraForgeLabs/infraforgelabs.github.io/main/meta/devopsmind/version.json"
)

# -------------------------------------------------
# Runtime helpers (IDENTICAL to start)
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


def _container_ready(name: str) -> bool:
    try:
        result = subprocess.run(
            ["docker", "exec", name, "sh", "-c", "true"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except Exception:
        return False


def _resolve_project_root(project_id: str) -> Path | None:
    for domain in LABS_DIR.iterdir():
        root = domain / "Projects" / project_id
        if root.exists():
            return root
    return None


# -------------------------------------------------
# 🚀 Command Handler
# -------------------------------------------------
def handle_project_resume(args):
    project_id = canonical_id(args.project_id)

    if project_id not in _available_project_ids():
        return boxed(
            "❌ Project Not Available",
            Text(f"Project '{project_id}' is not available.", style="red"),
        )

    workspace = WORKSPACE_ROOT / project_id
    if not workspace.exists():
        return boxed(
            "❌ Cannot Resume",
            Text(
                "No existing workspace found for this project.\n\n"
                f"Expected:\n{workspace}",
                style="red",
            ),
        )

    state = load_state()
    current = state.get("projects", {}).get(project_id)

    if current != "in-progress":
        return boxed(
            "❌ Cannot Resume",
            Text(
                f"Project is in '{current}' state and cannot be resumed.",
                style="red",
            ),
        )

    # -------------------------------------------------
    # 🔒 Runtime checks (IDENTICAL to start)
    # -------------------------------------------------
    required = _fetch_required_runtime_version()
    local = _local_runtime_version()
    image_present = required and _runtime_image_exists(required)

    if required and not image_present:
        return boxed(
            "⚠ Runtime Not Installed",
            Text(
                "DevOpsMind runtime is not installed.\n\n"
                f"Required runtime version : {required}\n\n"
                "Run:\n  devopsmind init",
                style="yellow",
            ),
        )

    if not required or local != required:
        return boxed(
            "⚠ Runtime Update Required",
            Text(
                "Your DevOpsMind runtime is outdated.\n\n"
                f"Installed version : {local or 'not installed'}\n"
                f"Required version  : {required or 'unknown'}\n\n"
                "Run:\n  devopsmind init",
                style="yellow",
            ),
        )

    project_root = _resolve_project_root(project_id)
    if not project_root:
        return boxed(
            "❌ Project Not Found",
            Text("Project definition not found.", style="red"),
        )

    meta = yaml.safe_load((project_root / "project.yaml").read_text()) or {}

    # -------------------------------------------------
    # Start project container
    # -------------------------------------------------
    container_name = start_project_container(
        project_id=project_id,
        workspace=workspace,
        project_source=project_root,
    )

    console.print(
        boxed(
            "⏳ Resuming Project Environment",
            Text(
                "🐳 Starting project container\n"
                "📂 Attaching existing workspace\n\n"
                "Please wait…",
                style="cyan",
            ),
        )
    )

    MAX_WAIT = 30
    start_time = time.time()

    while time.time() - start_time < MAX_WAIT:
        if _container_ready(container_name):
            break
        time.sleep(0.5)
    else:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return boxed(
            "❌ Resume Failed",
            Text("Project container did not become ready.", style="red"),
        )

    # -------------------------------------------------
    # 🎮 Launch safe project shell
    # -------------------------------------------------
    console.print(
        boxed(
            f"▶ Resumed Project · {project_id}",
            Text(
                "Workspace reattached successfully.\n\n"
                "Continue working on required artifacts.\n\n"
                f"When ready:\n  devopsmind project validate {project_id}",
                style="green",
            ),
        )
    )

    try:
        launch_safe_project_shell(
            workspace=workspace,
            project_id=project_id,
            stack=meta.get("stack", ""),
            session_id="project",
            container_name=container_name,
        )
    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
