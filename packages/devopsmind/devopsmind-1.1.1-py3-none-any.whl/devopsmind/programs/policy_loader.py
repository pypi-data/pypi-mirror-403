# src/devopsmind/programs/policy_loader.py

import json
from pathlib import Path
from datetime import date, datetime


POLICY_DIR = Path(__file__).parent / "policies"


def load_policy(program: str) -> dict | None:
    path = POLICY_DIR / f"{program}.policy.json"
    if not path.exists():
        return None

    with path.open() as f:
        return json.load(f)


def _parse_to_date(value: str) -> date:
    """
    Accepts:
      - YYYY-MM-DD
      - YYYY-MM-DDTHH:MM:SS
    Returns date object.
    """
    try:
        return date.fromisoformat(value)
    except ValueError:
        return datetime.fromisoformat(value).date()


def get_program_status(policy: dict) -> str:
    """
    Returns one of:
      - NOT_STARTED
      - ACTIVE
      - EXPIRED
    """
    window = policy.get("window")
    if not window:
        return "ACTIVE"  # fail-open for dev programs

    start = _parse_to_date(window["start"])
    end = _parse_to_date(window["end"])
    today = date.today()

    if today < start:
        return "NOT_STARTED"
    if today > end:
        return "EXPIRED"
    return "ACTIVE"
