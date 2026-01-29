from datetime import datetime, timezone
from pathlib import Path
import json
import math

# ------------------------------------------------------------
# Progress State Location (LOCKED)
# ------------------------------------------------------------
# ~/.devopsmind/programs/<program-id>/progress.json
# ------------------------------------------------------------

PROGRESS_ROOT = Path.home() / ".devopsmind" / "programs"
SECONDS_PER_DAY = 86400


def _progress_file(program_id: str) -> Path:
    return PROGRESS_ROOT / program_id / "progress.json"


def load_progress(program_id: str) -> dict:
    """
    Load progress metadata.
    Initializes started_at on first access.
    """
    file = _progress_file(program_id)
    file.parent.mkdir(parents=True, exist_ok=True)

    if not file.exists():
        data = {
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        file.write_text(json.dumps(data, indent=2))
        return data

    return json.loads(file.read_text())


def compute_progress_stage(program_id: str) -> int:
    """
    Compute relative progression stage (day-like),
    safe for late joiners.
    """
    data = load_progress(program_id)
    started_at = datetime.fromisoformat(data["started_at"])

    now = datetime.now(timezone.utc)
    elapsed = (now - started_at).total_seconds()

    stage = math.ceil(elapsed / SECONDS_PER_DAY)
    return max(1, stage)
