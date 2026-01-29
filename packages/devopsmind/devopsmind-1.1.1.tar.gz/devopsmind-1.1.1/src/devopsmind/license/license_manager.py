from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, Any


# ============================================================
# PATHS
# ============================================================

LICENSE_PATH = Path.home() / ".devopsmind" / "license.json"


# ============================================================
# DEFAULT FOUNDATION LICENSE (ALWAYS PRESENT)
# ============================================================

DEFAULT_FOUNDATION_LICENSE: Dict[str, Any] = {
    "product": "DevOpsMind",

    "edition": "foundation",
    "license_key": None,
    "license_type": "foundation",

    # Foundation is anonymous
    "owner_emails": [],

    "team": {
        "enabled": False,
        "max_users": 0,
        "members": []
    },

    "entitlements": {
        "core_pro": {
            "activated_at": None,
            "expires_at": None
        },
        "domains": {},
        "domain_plus": {},
        "certifications": {}
    },

    "license_history": [],

    "offline": True,
    "signature": None
}


# ============================================================
# UTILITIES
# ============================================================

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _entitlement_active(entry: Dict[str, Any]) -> bool:
    """
    Universal rule:
    - No expiry → active
    - Expired → inactive
    """
    expires_at = _parse_time(entry.get("expires_at"))
    if expires_at is None:
        return True
    return _now_utc() < expires_at


# ============================================================
# LOAD / SAVE
# ============================================================

def load_license() -> Dict[str, Any]:
    """
    Load license.json safely.

    HARD GUARANTEES:
    - Missing file → Foundation license
    - Corrupt file → Foundation license
    - Never raises
    """
    if not LICENSE_PATH.exists():
        return DEFAULT_FOUNDATION_LICENSE.copy()

    try:
        data = json.loads(LICENSE_PATH.read_text())
        if data.get("product") != "DevOpsMind":
            return DEFAULT_FOUNDATION_LICENSE.copy()
        return data
    except Exception:
        return DEFAULT_FOUNDATION_LICENSE.copy()


def save_license(license_data: Dict[str, Any]) -> None:
    """
    Atomic save. Never partially writes.
    """
    LICENSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = LICENSE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(license_data, indent=2))
    tmp.replace(LICENSE_PATH)


# ============================================================
# EMAIL RULES
# ============================================================

def email_required(license_data: Dict[str, Any]) -> bool:
    """
    Foundation is NOT email-bound.
    Everything else IS.
    """
    return license_data.get("license_type") != "foundation"


def email_allowed(license_data: Dict[str, Any], email: str) -> bool:
    if not email_required(license_data):
        return True
    return email in license_data.get("owner_emails", [])


# ============================================================
# ENTITLEMENT CHECKS
# ============================================================

def core_pro_active(license_data: Dict[str, Any]) -> bool:
    entry = license_data["entitlements"].get("core_pro")
    if not entry:
        return False
    return _entitlement_active(entry)


def domain_active(license_data: Dict[str, Any], domain: str) -> bool:
    entry = license_data["entitlements"]["domains"].get(domain)
    if not entry:
        return False
    return _entitlement_active(entry)


def domain_plus_active(license_data: Dict[str, Any], role: str) -> bool:
    entry = license_data["entitlements"]["domain_plus"].get(role)
    if not entry:
        return False
    return _entitlement_active(entry)


def certification_owned(license_data: Dict[str, Any], cert: str) -> bool:
    return cert in license_data["entitlements"]["certifications"]


# ============================================================
# ADD / MERGE ENTITLEMENTS (ADDITIVE ONLY)
# ============================================================

def add_core_pro(
    license_data: Dict[str, Any],
    activated_at: str,
    expires_at: Optional[str]
) -> None:
    license_data["edition"] = "pro"
    license_data["license_type"] = "core-pro"
    license_data["entitlements"]["core_pro"] = {
        "activated_at": activated_at,
        "expires_at": expires_at
    }


def add_domain(
    license_data: Dict[str, Any],
    domain: str,
    activated_at: str,
    expires_at: Optional[str]
) -> None:
    license_data["edition"] = "pro"
    license_data["entitlements"]["domains"][domain] = {
        "activated_at": activated_at,
        "expires_at": expires_at
    }


def add_domain_plus(
    license_data: Dict[str, Any],
    role: str,
    activated_at: str,
    expires_at: Optional[str]
) -> None:
    license_data["edition"] = "pro"
    license_data["entitlements"]["domain_plus"][role] = {
        "activated_at": activated_at,
        "expires_at": expires_at
    }


def add_certification(
    license_data: Dict[str, Any],
    cert: str,
    issued_at: str
) -> None:
    license_data["edition"] = "pro"
    license_data["entitlements"]["certifications"][cert] = {
        "issued_at": issued_at,
        "expires_at": None
    }


# ============================================================
# INSTALL PERMISSION (USED BY tier_installer)
# ============================================================

def can_install_core_pro(license_data: Dict[str, Any], email: str) -> bool:
    return (
        email_allowed(license_data, email)
        and core_pro_active(license_data)
    )


def can_install_domain(
    license_data: Dict[str, Any],
    domain: str,
    email: str
) -> bool:
    return (
        email_allowed(license_data, email)
        and domain_active(license_data, domain)
    )


def can_install_domain_plus(
    license_data: Dict[str, Any],
    role: str,
    email: str
) -> bool:
    return (
        email_allowed(license_data, email)
        and domain_plus_active(license_data, role)
    )


# ============================================================
# HUMAN-READABLE STATUS (CLI / UI)
# ============================================================

def license_summary(license_data: Dict[str, Any]) -> str:
    lines = []

    if license_data["license_type"] == "foundation":
        lines.append("DevOpsMind — Foundation Core (Free)")
        return "\n".join(lines)

    lines.append("DevOpsMind — Paid License")
    lines.append(f"Bound emails: {', '.join(license_data.get('owner_emails', []))}")

    if core_pro_active(license_data):
        lines.append("✔ Core Pro active")

    for d, entry in license_data["entitlements"]["domains"].items():
        state = "active" if _entitlement_active(entry) else "expired"
        lines.append(f"✔ Domain: {d} ({state})")

    for r, entry in license_data["entitlements"]["domain_plus"].items():
        state = "active" if _entitlement_active(entry) else "expired"
        lines.append(f"✔ Domain+ Role: {r} ({state})")

    for c in license_data["entitlements"]["certifications"]:
        lines.append(f"✔ Certification: {c}")

    return "\n".join(lines)
