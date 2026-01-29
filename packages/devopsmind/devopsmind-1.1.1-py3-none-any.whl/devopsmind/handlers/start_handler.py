from pathlib import Path
import subprocess
import json
import urllib.request
import time
import shutil   # ← ADDITIVE

from rich.console import Console
from rich.text import Text
from rich.prompt import Confirm

from devopsmind.engine.engine import start
from devopsmind.handlers.ui_helpers import boxed
from devopsmind.safety.safe_shell import launch_safe_shell
from devopsmind.list.lab_resolver import (
    get_all_labs,
    find_lab_by_id,
)
from devopsmind.runtime.lab_container import start_lab_container

# -------------------------------------------------
# 🔒 ADDITIVE: env handler 
# -------------------------------------------------
from devopsmind.handlers.start_env import run_env_and_capture_secrets

# -------------------------------------------------
# 🔒 ADDITIVE: difficulty gate
# -------------------------------------------------
from devopsmind.handlers.lab_gate import enforce_difficulty_gate
from devopsmind.progress import load_state

console = Console()

# -------------------------------------------------
# Runtime version source (RUNTIME ONLY)
# -------------------------------------------------
VERSION_URL = (
    "https://raw.githubusercontent.com/"
    "InfraForgeLabs/infraforgelabs.github.io/main/meta/devopsmind/version.json"
)

RUNTIME_VERSION_FILE = Path.home() / ".devopsmind" / "runtime_version"
STATE_FILE = Path.home() / ".devopsmind" / "state.json"
WORKSPACE_ROOT = Path.home() / "workspace"


# -------------------------------------------------
# Runtime helpers
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


# -------------------------------------------------
# 📜 ADDITIVE: optional doctrine resolver
# -------------------------------------------------
def _find_doctrine(lab_source: Path) -> Path | None:
    docs = lab_source / "docs"
    if not docs.exists():
        return None

    for f in docs.iterdir():
        if f.name.endswith("-doctrine.md"):
            return f

    return None


# -------------------------------------------------
# 🚀 PUBLIC ENTRYPOINT
# -------------------------------------------------
def handle_start(args, console: Console = console):
    console.clear()

    lab_id = args.id
    workspace = WORKSPACE_ROOT / lab_id
    display_path = f"~/workspace/{lab_id}"

    # -------------------------------------------------
    # 🔒 Runtime checks FIRST (authoritative)
    # -------------------------------------------------
    required = _fetch_required_runtime_version()
    local = _local_runtime_version()
    image_present = required and _runtime_image_exists(required)

    if required and not image_present:
        console.print(
            boxed(
                "⚠ Runtime Not Installed",
                Text(
                    "DevOpsMind runtime is not installed on this system.\n\n"
                    f"Required runtime version : {required}\n\n"
                    "Run:\n\n"
                    "  devopsmind init",
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
                    "Run:\n\n"
                    "  devopsmind init",
                    style="yellow",
                ),
            )
        )
        return

    # -------------------------------------------------
    # Workspace exists → suggest resume or reset
    # -------------------------------------------------
    if workspace.exists():
        console.print(
            boxed(
                "▶ Lab Already Started",
                Text(
                    "A workspace for this lab already exists.\n\n"
                    f"📂 {display_path}\n\n"
                    "Choose one:\n\n"
                    f"▶ Resume where you left off:\n"
                    f"  devopsmind resume {lab_id}\n\n"
                    f"♻ Start fresh (delete all progress):\n"
                    f"  devopsmind reset {lab_id}",
                    style="yellow",
                ),
            )
        )
        return

    # -------------------------------------------------
    # 🔒 LOAD LAB METADATA ONLY (NO SIDE EFFECTS)
    # -------------------------------------------------
    lab_source = find_lab_by_id(lab_id)
    if not lab_source:
        console.print(
            boxed(
                "❌ Start Failed",
                Text(f"Lab '{lab_id}' not found.", style="red"),
            )
        )
        return

    from devopsmind.handlers.lab_utils import load_lab_metadata
    lab_meta = load_lab_metadata(lab_source)

    # ---------------------------------------------------------
    # 🔒 Difficulty gate MUST run BEFORE start()
    # ---------------------------------------------------------
    state = load_state()

    if not enforce_difficulty_gate(
        state=state,
        lab_id=lab_id,
        stack=lab_meta.get("stack"),
        difficulty=lab_meta.get("difficulty"),
    ):
        return

    # -------------------------------------------------
    # Load lab context (SAFE AFTER GATE)
    # -------------------------------------------------
    context, message = start(lab_id)
    if not context:
        console.print(
            boxed("❌ Start Failed", Text(message, style="red"))
        )
        return

    # -------------------------------------------------
    # 📜 ADDITIVE: optional doctrine reference (bullet format)
    # Inserted ABOVE footer commands
    # -------------------------------------------------
    doctrine = _find_doctrine(lab_source)
    if doctrine:
        rel_path = doctrine.relative_to(lab_source)

        doctrine_block = (
            "\n📜 Doctrine reference (recommended reading before starting):\n"
            f"- {rel_path}\n"
        )

        footer_anchor = "\n\nRun `devopsmind describe` for details."

        if footer_anchor in message:
            message = message.replace(
                footer_anchor,
                doctrine_block + footer_anchor,
            )

    # -------------------------------------------------
    # Start per-lab container
    # -------------------------------------------------
    container_name = start_lab_container(
        lab_id=lab_id,
        workspace=context["workspace"],
        lab_source=lab_source,
        session_id=context["session_id"],
    )

    # -------------------------------------------------
    # ⏳ Waiting for runtime container
    # -------------------------------------------------
    console.print(
        boxed(
            "⏳ Preparing Lab Environment",
            Text(
                "📂 Preparing workspace\n"
                "🐳 Starting lab container\n\n"
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
        console.print(
            boxed(
                "❌ Environment Startup Failed",
                Text(
                    "The lab container did not become ready in time.\n\n"
                    "Try:\n"
                    "  devopsmind start <id>\n"
                    "or:\n"
                    "  devopsmind init",
                    style="red",
                ),
            )
        )
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return

    # -------------------------------------------------
    # 🧪 Environment setup (env/env.py) – FULLY DELEGATED
    # -------------------------------------------------
    ok, err = run_env_and_capture_secrets(
        lab_id=lab_id,
        container_name=container_name,
        lab_source=lab_source,
        workspace=context["workspace"],
        execution=context.get("execution", {}),
    )

    if not ok:
        console.print(
            boxed(
                "❌ Environment Setup Failed",
                Text(err, style="red"),
            )
        )
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return

    # -------------------------------------------------
    # 🎮 Start UI + 🔒 Safe Shell (WITH CLEANUP)
    # -------------------------------------------------
    console.print(
        boxed(
            f"🎮 Start · {lab_id}",
            Text(message),
        )
    )

    try:
        launch_safe_shell(
            workspace=context["workspace"],
            lab_id=context["lab_id"],
            stack=context["stack"],
            session_id=context["session_id"],
            container_name=container_name,
            safety_overrides=context["safety"],
        )
    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
