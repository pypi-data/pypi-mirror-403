import time
from rich.panel import Panel
from rich.text import Text
from rich.console import Console

from packaging.version import Version

from .update_check import check_for_update
from devopsmind.state import load_state, save_state
from devopsmind.constants import VERSION

console = Console()

CHECK_INTERVAL = 24 * 60 * 60  # seconds


def maybe_notify_update():
    """
    Display update notification if:
    - update exists (cached or newly detected)
    - last notification was more than 24 hours ago

    IMPORTANT POLICY:
    - Update checks are ALLOWED in offline mode
    - Offline mode blocks user data sync, NOT public metadata fetches
    """

    state = load_state()
    now = time.time()

    # -------------------------------------------------
    # 🧾 Persist current app version (UX / diagnostics)
    # -------------------------------------------------
    state.setdefault("app", {})
    state["app"]["current_version"] = VERSION
    save_state(state)

    # -------------------------------------------------
    # 🔁 Clear stale update cache after upgrade
    # -------------------------------------------------
    cached = state.get("available_update")
    if cached:
        try:
            cached_version = cached.get("version")
            if cached_version and Version(cached_version) <= Version(VERSION):
                state["available_update"] = None
                state["last_update_notify"] = None
                save_state(state)
                cached = None
        except Exception:
            pass

    # -------------------------------------------------
    # 1️⃣ Notify cached update (THROTTLED)
    # -------------------------------------------------
    last_notified = state.get("last_update_notify", 0)

    if cached and now - last_notified >= CHECK_INTERVAL:
        console.print(
            Panel(
                Text(
                    f"⬆ Update available: v{VERSION} → v{cached['version']}\n\n"
                    f"{cached.get('notes','')}\n\n"
                    "Run `pipx upgrade devopsmind` to update.",
                    style="bold",
                ),
                title="What's New",
                border_style="cyan",
            )
        )
        state["last_update_notify"] = now
        save_state(state)
        return  # ✅ CRITICAL: stop here

    # -------------------------------------------------
    # 2️⃣ Throttle network checks
    # -------------------------------------------------
    last_checked = state.get("last_update_check", 0)
    if now - last_checked < CHECK_INTERVAL:
        return

    # -------------------------------------------------
    # 3️⃣ Network check (ALLOWED in offline mode)
    # -------------------------------------------------
    try:
        has_update, latest, notes = check_for_update()
    except Exception:
        return

    state["last_update_check"] = now

    if not has_update:
        save_state(state)
        return

    # -------------------------------------------------
    # 4️⃣ Cache update info
    # -------------------------------------------------
    state["available_update"] = {
        "version": latest,
        "notes": notes,
        "detected_at": now,
    }
    save_state(state)

    # -------------------------------------------------
    # 5️⃣ Immediate notify (first detection)
    # -------------------------------------------------
    console.print(
        Panel(
            Text(
                f"⬆ Update available: v{VERSION} → v{latest}\n\n"
                f"{notes}\n\n"
                "Run `pipx upgrade devopsmind` to update.",
                style="bold",
            ),
            title="What's New",
            border_style="cyan",
        )
    )

    state["last_update_notify"] = now
    save_state(state)
