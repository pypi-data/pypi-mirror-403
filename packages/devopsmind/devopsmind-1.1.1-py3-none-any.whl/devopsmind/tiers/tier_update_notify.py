import time
import requests
from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from devopsmind.progress import load_state, save_state
from devopsmind.license.license_manager import (
    load_license,
    core_pro_active,
    domain_active,
    domain_plus_active,
)

console = Console()

# -------------------------------------------------
# Public metadata (NO user data, NO auth)
# -------------------------------------------------
TIER_RELEASE_META_URL = (
    "https://raw.githubusercontent.com/"
    "InfraForgeLabs/infraforgelabs.github.io/"
    "main/meta/devopsmind/tier_releases.json"
)

CHECK_INTERVAL = 24 * 60 * 60  # 24 hours


def _license_allows_tier(license_data: dict, tier: str) -> bool:
    """
    Determine if license is ACTIVE for a given tier.
    """
    if tier == "core_pro":
        return core_pro_active(license_data)

    if tier.startswith("domain_plus_"):
        role = tier.removeprefix("domain_plus_")
        return domain_plus_active(license_data, role)

    if tier.startswith("domain_"):
        domain = tier.removeprefix("domain_")
        return domain_active(license_data, domain)

    return False


def maybe_notify_tier_updates() -> None:
    """
    Notify users about new tier versions.

    RULES (LOCKED):
    - Notify ONLY owned tiers
    - Notify ONLY when a NEW version exists
    - Message depends on license state
    - NEVER modify ownership
    - NEVER block execution
    - Offline-safe
    """

    try:
        state = load_state() or {}
        now = time.time()

        state.setdefault("tier_updates", {})
        last_checked = state.get("last_tier_update_check", 0)

        if now - last_checked < CHECK_INTERVAL:
            return

        owned = state.get("tiers", {}).get("owned", {})
        if not isinstance(owned, dict) or not owned:
            return

        license_data = load_license()

        # -------------------------------------------------
        # Fetch public tier release metadata
        # -------------------------------------------------
        try:
            r = requests.get(TIER_RELEASE_META_URL, timeout=5)
            r.raise_for_status()
            releases = r.json().get("releases", [])
        except Exception:
            return

        # -------------------------------------------------
        # Process releases
        # -------------------------------------------------
        for release in releases:
            tier = release.get("tier")
            released_at = release.get("released_at")
            summary = release.get("summary", "")
            version = release.get("version")

            if not tier or not released_at or not isinstance(version, int):
                continue

            # Only notify for owned tiers
            if tier not in owned:
                continue

            owned_version = owned[tier].get("version")
            if not isinstance(owned_version, int):
                continue

            # No update if already earned
            if version <= owned_version:
                continue

            seen = state["tier_updates"].get(tier)
            if seen and seen.get("last_version_seen") == version:
                continue

            eligible = _license_allows_tier(license_data, tier)

            if eligible:
                console.print(
                    Panel(
                        Text(
                            f"🆕 New labs released for {tier}\n\n"
                            f"{summary}\n\n"
                            "Your license is active — these labs will be "
                            "permanently added to your ownership.",
                            style="bold",
                        ),
                        title="New Labs Available",
                        border_style="green",
                    )
                )
                status = "eligible"
            else:
                console.print(
                    Panel(
                        Text(
                            f"ℹ️ New labs released for {tier}\n\n"
                            f"{summary}\n\n"
                            "Your license expired before this release.\n"
                            "Renew to earn these labs permanently.\n\n"
                            "Previously earned labs remain available.",
                            style="bold",
                        ),
                        title="Content Update",
                        border_style="yellow",
                    )
                )
                status = "expired"

            state["tier_updates"][tier] = {
                "last_version_seen": version,
                "status": status,
            }

        state["last_tier_update_check"] = now
        save_state(state)

    except Exception:
        # Must NEVER block DevOpsMind
        pass
