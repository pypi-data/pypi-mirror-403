# src/devopsmind/tiers/loader.py
#
# ⚠️ LEGACY COMPATIBILITY LAYER
# DO NOT use this file for entitlement logic.
# All visibility is delegated to tier_loader.py.

from devopsmind.tiers.tier_loader import load_visible_lab_ids, list_owned_tiers


def load_owned_lab_ids() -> set[str]:
    """
    LEGACY API — DO NOT USE FOR NEW CODE

    Returns:
    - set of lab IDs visible to the user
    - delegated to tier_loader (authoritative)
    """
    return set(load_visible_lab_ids())


def load_owned_tiers() -> list[dict]:
    """
    LEGACY API — METADATA ONLY

    Returns:
    List of dicts with:
      - tier (id)
      - name (display name)

    Does NOT expose lab_ids to prevent entitlement leakage.
    """

    tiers = []
    for tier_name in list_owned_tiers():
        tiers.append({
            "tier": tier_name,
            "name": tier_name.replace("_", " ").title(),
        })

    return tiers
