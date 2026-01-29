from pathlib import Path
from datetime import datetime, timezone
import yaml

from devopsmind.handlers.id_normalizer import canonical_id
from devopsmind.progress import load_state


FOUNDATION_TIER_NAME = "foundation_core.yaml"


# -------------------------------------------------
# Internal helpers
# -------------------------------------------------

def _load_yaml_ids(path: Path) -> set[str]:
    """
    Load LAB IDs from a tier YAML file.

    HARD RULES:
    - ONLY lab_ids are visibility-bearing
    - project_ids NEVER affect visibility
    - Safe: never raises
    """
    try:
        data = yaml.safe_load(path.read_text()) or {}
        raw_ids = set(data.get("lab_ids", []))
        return {canonical_id(cid) for cid in raw_ids}
    except Exception:
        return set()


def _ensure_foundation_core_marker(bundled_core: Path):
    """
    Ensure Foundation Core marker exists in ~/.devopsmind/tiers/

    - Create ONCE
    - Heal incomplete marker
    - Never overwrite valid user-owned tiers
    - Never block execution
    """
    try:
        user_tiers_dir = Path.home() / ".devopsmind" / "tiers"
        user_tiers_dir.mkdir(parents=True, exist_ok=True)

        user_core = user_tiers_dir / FOUNDATION_TIER_NAME

        if not bundled_core.exists():
            return

        if not user_core.exists():
            user_core.write_text(bundled_core.read_text())
            return

        # 🔒 HEAL: file exists but is incomplete (no lab_ids)
        data = yaml.safe_load(user_core.read_text()) or {}
        if not data.get("lab_ids"):
            user_core.write_text(bundled_core.read_text())

    except Exception:
        pass


def _parse_version(path: Path) -> int:
    try:
        return int(path.stem.split("_v")[-1])
    except Exception:
        return 1


def _find_latest_version_yaml(tier_dir: Path) -> Path | None:
    candidates = sorted(
        tier_dir.glob("*_v*.yaml"),
        key=_parse_version,
    )
    return candidates[-1] if candidates else None


def _find_version_yaml(tier_dir: Path, version: int) -> Path | None:
    for f in tier_dir.glob(f"*_v{version}.yaml"):
        return f
    return None


def _resolve_tier_yaml(tier_name: str, meta: dict, expired: bool) -> Path | None:
    """
    Resolve which YAML file to load for a tier.
    """

    base_dir = Path(__file__).parent

    if tier_name == "core_pro":
        tier_dir = base_dir / "core_pro"

    elif tier_name.startswith("domain_plus_"):
        role = tier_name.removeprefix("domain_plus_")
        tier_dir = base_dir / role

    elif tier_name.startswith("domain_"):
        domain = tier_name.removeprefix("domain_")
        tier_dir = base_dir / domain

    else:
        return None

    if not tier_dir.exists():
        return None

    # 🔒 Expired → frozen version
    if expired and "version" in meta:
        return _find_version_yaml(tier_dir, meta["version"])

    # ✅ Active → latest version
    return _find_latest_version_yaml(tier_dir)


# -------------------------------------------------
# Tier visibility resolution (AUTHORITATIVE)
# -------------------------------------------------

def _resolve_user_tier_ids() -> set[str]:
    """
    Resolve LAB IDs for user-owned tiers with tier-level expiry.

    RULES:
    - Tier expiry is authoritative
    - Expired tier → stored version
    - Active tier → latest version
    - Legacy frozen_labs supported
    - No tier is ever removed
    - Offline-safe
    """

    state = load_state() or {}
    owned = state.get("tiers", {}).get("owned", {})

    now = datetime.now(timezone.utc)
    resolved: set[str] = set()

    # Backward compatibility: owned may be list[str]
    if isinstance(owned, list):
        user_tiers_dir = Path.home() / ".devopsmind" / "tiers"
        for tier_name in owned:
            tier_file = user_tiers_dir / f"{tier_name}.yaml"
            resolved |= _load_yaml_ids(tier_file)
        return resolved

    for tier_name, meta in owned.items():
        expires_at = meta.get("expires_at")
        expired = False

        if expires_at:
            try:
                exp = datetime.fromisoformat(
                    expires_at.replace("Z", "+00:00")
                )
                expired = now > exp
            except Exception:
                expired = True

        # -------------------------------------------------
        # Legacy support: frozen_labs
        # -------------------------------------------------
        if expired and "frozen_labs" in meta:
            resolved |= {canonical_id(cid) for cid in meta.get("frozen_labs", [])}
            continue

        # -------------------------------------------------
        # Versioned tier resolution
        # -------------------------------------------------
        tier_yaml = _resolve_tier_yaml(tier_name, meta, expired)
        if tier_yaml and tier_yaml.exists():
            resolved |= _load_yaml_ids(tier_yaml)

    return resolved


# -------------------------------------------------
# Public API
# -------------------------------------------------

def load_foundation_core_ids() -> set[str]:
    """
    Load all LAB IDs visible to the user.

    GUARANTEES:
    - Foundation Core is always visible
    - Paid tiers respect tier-level expiry
    - Version-aware
    - No project leakage
    - Deterministic
    - Offline-safe
    """

    bundled_ids: set[str] = set()
    bundled_dir = Path(__file__).parent
    bundled_core = bundled_dir / "foundation_core" / FOUNDATION_TIER_NAME

    # Foundation Core is always live
    if bundled_core.exists():
        bundled_ids |= _load_yaml_ids(bundled_core)

    _ensure_foundation_core_marker(bundled_core)

    user_ids = _resolve_user_tier_ids()

    return bundled_ids | user_ids


def load_visible_lab_ids() -> set[str]:
    """
    SINGLE SOURCE OF TRUTH for lab visibility.
    """
    return load_foundation_core_ids()


def list_owned_tiers() -> list[str]:
    """
    Return owned tier names.
    """
    state = load_state() or {}
    owned = state.get("tiers", {}).get("owned", {})
    return sorted(owned.keys()) if isinstance(owned, dict) else owned


def user_has_projects() -> bool:
    """
    Return True if user owns at least one project (capstone).

    - project_ids NEVER affect lab visibility
    - UI / discovery helper only
    """
    tiers_dir = Path.home() / ".devopsmind" / "tiers"
    if not tiers_dir.exists():
        return False

    for tier_file in tiers_dir.rglob("*.yaml"):
        try:
            data = yaml.safe_load(tier_file.read_text()) or {}
            project_ids = data.get("project_ids") or []
            if isinstance(project_ids, list) and project_ids:
                return True
        except Exception:
            continue

    return False


# -------------------------------------------------
# UI helpers — future-proof
# -------------------------------------------------

def list_owned_stack_domains() -> dict[str, str]:
    """
    Return owned stack domains as:
      { "<cli-flag>": "<display name>" }

    Uses YAML metadata only.
    """

    domains = {}
    tiers_dir = Path.home() / ".devopsmind" / "tiers"

    if not tiers_dir.exists():
        return domains

    for f in tiers_dir.rglob("*.yaml"):
        try:
            data = yaml.safe_load(f.read_text()) or {}

            if not data.get("lab_ids"):
                continue

            display_name = data.get("name")
            if not display_name:
                continue

            stem = f.stem

            if stem.startswith("foundation_core"):
                flag = "foundation"
            else:
                flag = (
                    stem
                    .split("_v")[0]
                    .replace("domain_plus_", "")
                    .replace("domain_", "")
                    .replace("_", "-")
                )

            domains[flag] = display_name

        except Exception:
            continue

    return domains
