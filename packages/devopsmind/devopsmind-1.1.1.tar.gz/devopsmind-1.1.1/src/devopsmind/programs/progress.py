import json
from pathlib import Path
from datetime import datetime, timezone

PROGRESS_ROOT = Path.home() / ".devopsmind" / "programs"

DEFAULT_PROGRESS = {
    "started_at": None,
    "systems": {
        "execution": 0,
        "resilience": 0,
        "delivery": 0,
    },
    "earned": {}
}

def _progress_file(program_id: str) -> Path:
    return PROGRESS_ROOT / program_id / "progress.json"


def load_progress(program_id: str) -> dict:
    path = _progress_file(program_id)

    if not path.exists():
        progress = DEFAULT_PROGRESS.copy()
        progress["started_at"] = datetime.now(timezone.utc).isoformat()
        save_progress(program_id, progress)
        return progress

    return json.loads(path.read_text())


def save_progress(program_id: str, progress: dict) -> None:
    path = _progress_file(program_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(progress, indent=2))


# ------------------------------------------------------------
# PARTIAL PROGRESS (AUTHORITATIVE)
# ------------------------------------------------------------

def award_partial_progress(
    program_id: str,
    system: str,
    key: str,
    amount: int,
) -> bool:
    """
    Award progress ONCE per (system + key).
    """
    progress = load_progress(program_id)

    earned = progress.setdefault("earned", {})
    system_earned = earned.setdefault(system, [])

    if key in system_earned:
        return False  # already earned

    progress["systems"][system] = min(
        100,
        progress["systems"].get(system, 0) + amount
    )

    system_earned.append(key)
    save_progress(program_id, progress)
    return True
