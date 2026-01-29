from pathlib import Path
from datetime import datetime, timezone
import yaml

from devopsmind.progress import load_state, save_state
from devopsmind.license.license_manager import load_license


BASE_DIR = Path(__file__).parent
USER_TIERS_DIR = Path.home() / ".devopsmind" / "tiers"


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def _parse_version(path: Path) -> int:
    try:
        return int(path.stem.split("_v")[-1])
    except Exception:
        return 1


def _find_latest_yaml(tier_dir: Path) -> tuple[Path, int] | tuple[None, None]:
    candidates = sorted(
        tier_dir.glob("*_v*.yaml"),
        key=_parse_version,
    )

    if not candidates:
        return None, None

    latest = candidates[-1]
    return latest, _parse_version(latest)


def _license_active(expires_at: str | None) -> bool:
    if not expires_at:
        return False
    try:
        exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) <= exp
    except Exception:
        return False


def _resolve_tier_dir(tier_name: str) -> Path | None:
    if tier_name == "core_pro":
        return BASE_DIR / "core_pro"

    if tier_name.startswith("domain_plus_"):
        role = tier_name.removeprefix("domain_plus_")
        return BASE_DIR / role

    if tier_name.startswith("domain_"):
        domain = tier_name.removeprefix("domain_")
        return BASE_DIR / domain

    return None


# -------------------------------------------------
# Migration (earned entitlement model)
# -------------------------------------------------

def migrate_paid_tiers_visibility_if_active() -> None:
    """
    PAID TIER VERSION MIGRATION (EARNED OWNERSHIP)

    RULES:
    - While license is ACTIVE:
        • Replace user tier YAML with latest version
        • Bump state.json version upward (earned permanently)
    - When license is EXPIRED:
        • Do NOTHING
        • Ownership remains frozen at highest earned version
    - Never install new tiers
    - Never downgrade versions
    - Never touch foundation_core
    - Offline-safe, best-effort
    """

    try:
        if not USER_TIERS_DIR.exists():
            return

        state = load_state() or {}
        tiers = state.setdefault("tiers", {})
        owned = tiers.setdefault("owned", {})

        if not isinstance(owned, dict):
            return

        license_data = load_license()
        state_changed = False

        for tier_name, meta in owned.items():
            # ---------------------------------------------
            # Skip foundation
            # ---------------------------------------------
            if tier_name == "foundation_core":
                continue

            # ---------------------------------------------
            # License must be active
            # ---------------------------------------------
            if not _license_active(meta.get("expires_at")):
                continue

            current_version = meta.get("version")
            if not isinstance(current_version, int):
                continue

            # ---------------------------------------------
            # Resolve tier directory
            # ---------------------------------------------
            tier_dir = _resolve_tier_dir(tier_name)
            if not tier_dir or not tier_dir.exists():
                continue

            latest_yaml, latest_version = _find_latest_yaml(tier_dir)
            if not latest_yaml:
                continue

            # ---------------------------------------------
            # Earn new version if higher
            # ---------------------------------------------
            if latest_version > current_version:
                # 1️⃣ Replace user YAML (active content)
                try:
                    user_yaml = USER_TIERS_DIR / latest_yaml.name
                    tmp = user_yaml.with_suffix(".tmp")
                    tmp.write_text(latest_yaml.read_text())
                    tmp.replace(user_yaml)
                except Exception:
                    continue

                # 2️⃣ Permanently bump owned version
                meta["version"] = latest_version
                state_changed = True

        if state_changed:
            save_state(state)

    except Exception:
        # Must NEVER break DevOpsMind
        pass
