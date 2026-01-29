from pathlib import Path
import yaml

from devopsmind.license_manager import (
    can_install_core_pro,
    can_install_domain,
    can_install_domain_plus,
)

from devopsmind.progress import load_state, save_state


# ------------------------------------------------------------
# Tier name conventions (LOCKED)
#
# foundation_core (handled elsewhere)
# core_pro
# domain_<name>           (cloudops, security, observability, aiops, scenarios, story)
# domain_plus_<role>      (linux, python)
# ------------------------------------------------------------


def _resolve_latest_tier_yaml(tier_name: str) -> tuple[Path, int] | tuple[None, None]:
    """
    Resolve the latest versioned YAML for a tier.

    Returns:
        (yaml_path, version)
    """
    base_dir = Path(__file__).parent

    # Tier directories are organized by domain / role
    if tier_name == "core_pro":
        tier_dir = base_dir / "core_pro"

    elif tier_name.startswith("domain_plus_"):
        role = tier_name.removeprefix("domain_plus_")
        tier_dir = base_dir / role

    elif tier_name.startswith("domain_"):
        domain = tier_name.removeprefix("domain_")
        tier_dir = base_dir / domain

    else:
        return None, None

    if not tier_dir.exists():
        return None, None

    candidates = sorted(
        tier_dir.glob(f"{tier_name}_v*.yaml"),
        key=lambda p: int(p.stem.split("_v")[-1]),
    )

    if not candidates:
        return None, None

    latest = candidates[-1]

    try:
        meta = yaml.safe_load(latest.read_text()) or {}
        version = int(meta.get("version", 1))
    except Exception:
        version = 1

    return latest, version


def install_tier_if_allowed(
    tier_name: str,
    license_data: dict,
    user_email: str
) -> bool:
    """
    Install a tier if allowed by license.

    GUARANTEES:
    - Foundation Core is NEVER installed here
    - Tier YAML is copied ONCE
    - Ownership is permanent
    - Installer NEVER mutates on expiry
    - Version is frozen at install time
    - Loader decides visibility later
    - Offline-safe
    """

    # --------------------------------------------------------
    # Foundation handled elsewhere
    # --------------------------------------------------------
    if tier_name == "foundation_core":
        return False

    # --------------------------------------------------------
    # License entitlement checks
    # --------------------------------------------------------
    if tier_name == "core_pro":
        allowed = can_install_core_pro(license_data, user_email)

    elif tier_name.startswith("domain_plus_"):
        role = tier_name.removeprefix("domain_plus_")
        allowed = can_install_domain_plus(license_data, role, user_email)

    elif tier_name.startswith("domain_"):
        domain = tier_name.removeprefix("domain_")
        allowed = can_install_domain(license_data, domain, user_email)

    else:
        return False

    if not allowed:
        return False

    # --------------------------------------------------------
    # Resolve latest versioned YAML
    # --------------------------------------------------------
    bundled_yaml, bundled_version = _resolve_latest_tier_yaml(tier_name)
    if not bundled_yaml:
        return False

    # --------------------------------------------------------
    # Install YAML into user tiers (ownership marker)
    # --------------------------------------------------------
    user_tiers = Path.home() / ".devopsmind" / "tiers"
    user_tiers.mkdir(parents=True, exist_ok=True)

    target = user_tiers / bundled_yaml.name

    if not target.exists():
        try:
            tmp = target.with_suffix(".tmp")
            tmp.write_text(bundled_yaml.read_text())
            tmp.replace(target)
        except Exception:
            return False

    # --------------------------------------------------------
    # Record ownership in STATE (AUTHORITATIVE)
    # --------------------------------------------------------
    try:
        state = load_state() or {}

        tiers = state.setdefault("tiers", {})
        owned = tiers.setdefault("owned", {})

        # Backward compatibility (old list format)
        if isinstance(owned, list):
            owned = {t: {} for t in owned}
            tiers["owned"] = owned

        # DO NOT overwrite existing ownership
        if tier_name not in owned:
            owned[tier_name] = {
                "version": bundled_version,
                "expires_at": license_data.get("expires_at"),
            }

        save_state(state)

    except Exception:
        return False

    return True
