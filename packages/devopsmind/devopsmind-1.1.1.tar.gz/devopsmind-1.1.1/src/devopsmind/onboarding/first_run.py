from rich.panel import Panel
from rich.text import Text
from rich.console import Console
import getpass
import random
from datetime import date
from pathlib import Path
import yaml

from devopsmind.state import (
    is_first_run,
    save_state,
    load_state,
    mark_session_unlocked,
    get_restore_decision,
    set_restore_decision,
)
from devopsmind.restore.snapshot import snapshot_exists, restore_snapshot
from .remote import authenticate_with_worker
from devopsmind.restore.cloud_restore import maybe_prompt_cloud_restore
from devopsmind.stats import stats

# 🔹 Fire-and-forget telemetry (anonymous counters)
from .telemetry import send_event

# 🔹 Docker reuse from doctor
from devopsmind.doctor import docker_installed, docker_install_hint

console = Console()

TIERS_DIR = Path.home() / ".devopsmind" / "tiers"


# =================================================
# BUILDTRACK — TIME-BOUND HELPERS
# =================================================
def _is_buildtrack_window():
    today = date.today()
    start = date(today.year, 2, 14)
    end = date(today.year, 2, 28)
    return start <= today <= end


def show_buildtrack_pre_auth_notice():
    if not _is_buildtrack_window():
        return

    message = (
        "🏁 BuildTrack Program Active\n\n"
        "This BuildTrack requires ONLINE mode\n"
        "to track progress and issue certificates."
    )

    console.print(
        Panel(
            Text(message, justify="center"),
            title="📘 BuildTrack",
            border_style="cyan",
        )
    )


def show_buildtrack_post_login_commands():
    if not _is_buildtrack_window():
        return

    message = (
        "BuildTrack commands:\n\n"
        "  devopsmind programs\n"
        "  devopsmind program buildtrack\n"
    )

    console.print(
        Panel(
            Text(message, justify="center"),
            title="📘 BuildTrack",
            border_style="green",
        )
    )


def suggest_handles(base: str) -> list[str]:
    suffixes = [
        "_dev",
        "_ops",
        "_infra",
        "_cloud",
        "_sec",
        "_x",
        f"_{random.randint(1,99)}",
        f"{random.randint(1,99)}",
    ]
    return [f"{base}{s}" for s in suffixes][:5]


def show_post_login_instructions():
    if docker_installed():
        message = (
            "🐳 Docker detected ✔\n\n"
            "DevOpsMind runs real-world labs in isolated containers.\n\n"
            "Next step:\n"
            "  devopsmind init\n\n"
            "This will prepare your local environment."
        )
        title = "🚀 Ready to Go"
        border = "green"
    else:
        message = (
            "⚠ Docker is required\n\n"
            "DevOpsMind uses Docker for real-world labs.\n\n"
            f"{docker_install_hint()}\n\n"
            "After installation, run:\n"
            "  devopsmind init"
        )
        title = "🧰 Setup Required"
        border = "yellow"

    console.print(
        Panel(
            Text(message, justify="center"),
            title=title,
            border_style=border,
        )
    )


# =================================================
# 🔒 TIER MATERIALIZATION INTEGRITY (ADDITIVE)
# =================================================
def _ensure_owned_tiers_materialized(state: dict):
    """
    Ensure every owned tier has a valid YAML with lab_ids.
    Silent, offline-safe, idempotent.
    """
    owned = state.get("tiers", {}).get("owned", {})
    if not owned:
        return

    TIERS_DIR.mkdir(parents=True, exist_ok=True)

    for tier_id in owned.keys():
        tier_file = TIERS_DIR / f"{tier_id}.yaml"

        if tier_file.exists():
            try:
                data = yaml.safe_load(tier_file.read_text()) or {}
                if isinstance(data.get("lab_ids"), list):
                    continue
            except Exception:
                pass  # fall through to repair

        # Minimal safe re-materialization (no lab leakage)
        tier_file.write_text(
            yaml.safe_dump(
                {
                    "tier": tier_id,
                    "name": tier_id.replace("_", " ").title(),
                    "lab_ids": [],
                }
            )
        )


# =================================================
# FIRST RUN FLOW
# =================================================
def ensure_first_run(force: bool = False) -> bool:
    """
    Returns True ONLY if:
    - Offline mode completed successfully OR
    - Online authentication (login OR signup) succeeded

    Returns False on ANY auth failure.
    """

    if not force and not is_first_run():
        return True

    console.print(
        Panel(
            Text(
                "Welcome to DevOpsMind 🚀\n\n"
                "DevOpsMind works fully offline by default.\n"
                "You decide if and when anything goes online.",
                justify="center",
            ),
            title="🧠 First Run Setup",
            border_style="cyan",
        )
    )

    show_buildtrack_pre_auth_notice()

    choice = input("Enable ONLINE mode now? [y/N]: ").strip().lower()

    # =================================================
    # OFFLINE MODE
    # =================================================
    if choice != "y":
        username = input("👤 Enter your full name: ").strip()
        handle = input("🎮 Choose a handle: ").strip()

        state = {
            "mode": "offline",
            "auth": {"lock_enabled": False},
            "profile": {
                "username": username,
                "gamer": handle,
            },
            "tiers": {"owned": {"foundation_core": {}}},
        }

        save_state(state)
        send_event("first_run_offline")

        show_post_login_instructions()
        return True

    # =================================================
    # ONLINE MODE
    # =================================================
    console.print(
        Panel(
            Text(
                "Online account options:\n\n"
                "1) Login / Signup\n"
                "2) Reset password (Recovery key)",
                justify="center",
            ),
            title="🔐 Online Account",
            border_style="cyan",
        )
    )

    action = input("Choose [1/2]: ").strip()
    if action not in ("1", "2"):
        return False

    email = input("📧 Email: ").strip().lower()

    # ---------------- PASSWORD RESET ----------------
    if action == "2":
        recovery_key = getpass.getpass("🔑 Recovery key: ")
        new_password = getpass.getpass("🔒 New password: ")

        result = authenticate_with_worker(
            email=email,
            mode="reset",
            recovery_key=recovery_key,
            new_password=new_password,
        )

        if result and result.get("ok"):
            console.print(Panel(Text("✔ Password reset successful"), border_style="green"))
        else:
            console.print(Panel(Text("❌ Password reset failed"), border_style="red"))
        return False

    # ---------------- LOGIN / SIGNUP ----------------
    password = getpass.getpass("🔒 Password: ")
    result = authenticate_with_worker(email=email, password=password, mode="login")

    if result and result.get("ok"):
        email_hash = result["email_hash"]
        user_public_id = result["user_public_id"]
        username = result["username"]
        handle = result["handle"]
    else:
        console.print(Panel(Text("❌ Login failed"), border_style="red"))
        return False

    snapshot_existed = snapshot_exists(user_public_id)

    state = load_state()
    state["mode"] = "online"
    state.setdefault("auth", {})["lock_enabled"] = True
    state["profile"] = {
        "username": username,
        "gamer": handle,
        "email": email,
        "email_hash": email_hash,
        "user_public_id": user_public_id,
    }
    state.setdefault("tiers", {}).setdefault("owned", {"foundation_core": {}})
    save_state(state)

    mark_session_unlocked()

    maybe_prompt_cloud_restore(user_public_id)

    if snapshot_existed:
        decision = get_restore_decision(user_public_id)

        if decision is None:
            decision = input("Restore cloud progress? [Y/n]: ").strip().lower() in (
                "",
                "y",
                "yes",
            )
            set_restore_decision(user_public_id, decision)

        if decision:
            local_email = state.get("profile", {}).get("email")
            restore_snapshot(user_public_id)

            state = load_state()
            if local_email:
                state.setdefault("profile", {})["email"] = local_email

            # 🔒 CRITICAL REPAIR (ONLY ADDITION)
            _ensure_owned_tiers_materialized(state)

            save_state(state)

    console.print(
        Panel(
            Text(
                "✔ Online login successful\n\n"
                "Next steps:\n"
                "  devopsmind\n"
                "  devopsmind stacks",
                justify="center",
            ),
            border_style="green",
        )
    )

    show_buildtrack_post_login_commands()
    show_post_login_instructions()

    send_event("first_run_online")
    send_event("first_login_online")
    return True
