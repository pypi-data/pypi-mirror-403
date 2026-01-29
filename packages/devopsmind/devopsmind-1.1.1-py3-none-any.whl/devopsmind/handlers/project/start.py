# src/devopsmind/handlers/project/start.py

from pathlib import Path
import subprocess
import json
import urllib.request
import time
import shutil
import uuid
import yaml

from rich.console import Console
from rich.text import Text

from devopsmind.handlers.ui_helpers import boxed
from devopsmind.handlers.id_normalizer import canonical_id
from devopsmind.runtime.project_container import start_project_container
from devopsmind.safety.safe_project_shell import launch_safe_project_shell
from devopsmind.state import load_state, save_state

console = Console()

# -------------------------------------------------
# Runtime version (LOCKED – same as labs)
# -------------------------------------------------
VERSION_URL = (
    "https://raw.githubusercontent.com/"
    "InfraForgeLabs/infraforgelabs.github.io/main/meta/devopsmind/version.json"
)

RUNTIME_VERSION_FILE = Path.home() / ".devopsmind" / "runtime_version"

# -------------------------------------------------
# Paths
# -------------------------------------------------
DEVOPSMIND_ROOT = Path(__file__).resolve().parents[2]
LABS_DIR = DEVOPSMIND_ROOT / "labs"
WORKSPACE_ROOT = Path.home() / "workspace" / "project"
TIERS_DIR = Path.home() / ".devopsmind" / "tiers"

# -------------------------------------------------
# Project copy exclusions (LOCKED)
# -------------------------------------------------
EXCLUDE_NAMES = {
    "project.yaml",
    "validator.py",
    "__pycache__",
    "description.md",
    "env",
    ".git",
    ".gitignore",
}

# -------------------------------------------------
# Runtime helpers (IDENTICAL TO LABS)
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
        return (
            subprocess.run(
                ["docker", "exec", name, "sh", "-c", "true"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        )
    except Exception:
        return False


# -------------------------------------------------
# 🔐 OWNED PROJECT RESOLUTION (AUTHORITATIVE)
# -------------------------------------------------
def _owned_project_ids() -> set[str]:
    """
    Resolve owned project IDs from user-materialized tier YAMLs.

    - Version-safe
    - License-safe
    - Snapshot-safe
    - Offline-safe
    """
    owned: set[str] = set()

    if not TIERS_DIR.exists():
        return owned

    for tier_file in TIERS_DIR.glob("*.yaml"):
        try:
            data = yaml.safe_load(tier_file.read_text()) or {}
            for pid in data.get("project_ids", []):
                if isinstance(pid, str):
                    owned.add(canonical_id(pid))
        except Exception:
            continue

    return owned


# -------------------------------------------------
# Project resolution
# -------------------------------------------------
def _resolve_project_root(project_id: str) -> Path | None:
    for domain in LABS_DIR.iterdir():
        root = domain / "Projects" / project_id
        if root.exists():
            return root
    return None


def _copy_project_files(src: Path, dst: Path):
    for item in src.iterdir():
        if item.name in EXCLUDE_NAMES:
            continue

        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


# -------------------------------------------------
# 🚀 PUBLIC ENTRYPOINT
# -------------------------------------------------
def handle_project_start(args):
    console.clear()

    if not args.project_id:
        console.print(
            boxed("❌ Project Start Failed", Text("Project ID required.", style="red"))
        )
        return

    project_id = canonical_id(args.project_id)
    workspace = WORKSPACE_ROOT / project_id
    display_path = f"~/workspace/project/{project_id}"

    # -------------------------------------------------
    # Runtime checks (AUTHORITATIVE)
    # -------------------------------------------------
    required = _fetch_required_runtime_version()
    local = _local_runtime_version()

    if required and not _runtime_image_exists(required):
        console.print(
            boxed(
                "⚠ Runtime Not Installed",
                Text(
                    "DevOpsMind runtime is not installed.\n\n"
                    f"Required runtime version : {required}\n\n"
                    "Run:\n  devopsmind init",
                    style="yellow",
                ),
            )
        )
        return

    if not required or local != required:
        console.print(
            boxed(
                "⚠ Runtime Update Required",
                Text(
                    "Your DevOpsMind runtime is outdated.\n\n"
                    f"Installed version : {local or 'not installed'}\n"
                    f"Required version  : {required or 'unknown'}\n\n"
                    "Run:\n  devopsmind init",
                    style="yellow",
                ),
            )
        )
        return

    # -------------------------------------------------
    # Workspace exists → resume / reset
    # -------------------------------------------------
    if workspace.exists():
        console.print(
            boxed(
                "▶ Project Already Started",
                Text(
                    "A workspace already exists for this project.\n\n"
                    f"📂 {display_path}\n\n"
                    "▶ Resume:\n"
                    f"  devopsmind project resume {project_id}\n\n"
                    "♻ Reset (destructive):\n"
                    f"  devopsmind project reset {project_id}",
                    style="yellow",
                ),
            )
        )
        return

    # -------------------------------------------------
    # 🔐 Availability gate (FIXED)
    # -------------------------------------------------
    if project_id not in _owned_project_ids():
        console.print(
            boxed(
                "❌ Cannot Start Project",
                Text(f"Project '{project_id}' is not available.", style="red"),
            )
        )
        return

    project_root = _resolve_project_root(project_id)
    if not project_root:
        console.print(
            boxed(
                "❌ Cannot Start Project",
                Text("Project definition not found.", style="red"),
            )
        )
        return

    # -------------------------------------------------
    # Load project.yaml (AUTHORITATIVE)
    # -------------------------------------------------
    project_yaml = project_root / "project.yaml"
    meta = yaml.safe_load(project_yaml.read_text()) or {}

    title = meta.get("title", project_id)
    goal = meta.get("goal", "").strip()
    artifacts = meta.get("artifacts", {}).get("required", [])

    # -------------------------------------------------
    # Prepare workspace
    # -------------------------------------------------
    workspace.mkdir(parents=True)
    _copy_project_files(project_root, workspace)

    # -------------------------------------------------
    # Mark project in-progress
    # -------------------------------------------------
    state = load_state()
    state.setdefault("projects", {})[project_id] = "in-progress"
    save_state(state)

    # -------------------------------------------------
    # Start project container
    # -------------------------------------------------
    session_id = uuid.uuid4().hex[:8]

    container_name = start_project_container(
        project_id=project_id,
        workspace=workspace,
        project_source=project_root,
        session_id=session_id,
    )

    console.print(
        boxed(
            "⏳ Preparing Project Environment",
            Text(
                "📂 Preparing workspace\n"
                "🐳 Starting project container\n\n"
                "Please wait…",
                style="cyan",
            ),
        )
    )

    start_time = time.time()
    while time.time() - start_time < 30:
        if _container_ready(container_name):
            break
        time.sleep(0.5)
    else:
        console.print(
            boxed(
                "❌ Project Startup Failed",
                Text("Project container did not become ready.", style="red"),
            )
        )
        subprocess.run(["docker", "rm", "-f", container_name])
        return

    # -------------------------------------------------
    # 🎮 FINAL START UI (PROJECT-SPECIFIC)
    # -------------------------------------------------
    artifact_lines = "\n".join(f"- {a}" for a in artifacts) if artifacts else "None"

    body = (
        f"Title: {title}\n\n"
        f"📂 Workspace:\n{display_path}\n\n"
        f"🎯 Goal:\n{goal}\n\n"
        f"📦 Required Artifacts:\n{artifact_lines}\n\n"
        "Run `devopsmind project describe` for details.\n"
        "Run `devopsmind project validate` when ready.\n\n"
        "🔒 Entering DevOpsMind Safe Shell…"
    )

    console.print(
        boxed(
            f"🎮 Start · {project_id}",
            Text(body),
        )
    )

    try:
        launch_safe_project_shell(
            workspace=workspace,
            project_id=project_id,
            stack=meta.get("stack", "project"),
            session_id=session_id,
            container_name=container_name,
        )
    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
