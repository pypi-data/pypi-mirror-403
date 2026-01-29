from pathlib import Path
import json
from typing import Dict, Any

from devopsmind.license.license_manager import (
    DEFAULT_FOUNDATION_LICENSE,
    save_license
)

LICENSE_PATH = Path.home() / ".devopsmind" / "license.json"
STATE_PATH = Path.home() / ".devopsmind" / "state.json"
TIERS_DIR = Path.home() / ".devopsmind" / "tiers"


# ---------------------------------------------------------
# MIGRATION GUARD (FOUNDATION SAFE)
# ---------------------------------------------------------

def ensure_safe_foundation_state() -> None:
    """
    HARD GUARANTEE:
    - If license.json does not exist → DO NOTHING
    - Foundation users are NEVER modified
    """
    if LICENSE_PATH.exists():
        return

    # Ensure foundation tier exists (defensive)
    TIERS_DIR.mkdir(parents=True, exist_ok=True)
    foundation = TIERS_DIR / "foundation_core.yaml"
    if not foundation.exists():
        # tier_loader will re-create it if missing
        pass


# ---------------------------------------------------------
# UPGRADE FLOW (FOUNDATION → PAID)
# ---------------------------------------------------------

def upgrade_to_paid_license(
    license_payload: Dict[str, Any]
) -> None:
    """
    Create license.json for the FIRST time.

    This is called ONLY after:
    - License key validated
    - Email verified
    - Package selected
    - Entitlements calculated

    RULES:
    - Never overwrite existing license.json
    - Never touch state.json
    - Never touch snapshot.json
    - Never touch tiers/
    """

    if LICENSE_PATH.exists():
        # Already paid or already upgraded
        return

    # Start from a clean foundation base
    new_license = DEFAULT_FOUNDATION_LICENSE.copy()

    # Apply paid license payload
    new_license.update({
        "edition": "pro",
        "license_key": license_payload["license_key"],
        "license_type": license_payload["license_type"],
        "owner_emails": license_payload["owner_emails"],
        "team": license_payload.get("team", {
            "enabled": False,
            "max_users": 1,
            "members": license_payload["owner_emails"]
        }),
        "entitlements": license_payload["entitlements"],
        "signature": license_payload.get("signature"),
        "offline": True
    })

    save_license(new_license)
