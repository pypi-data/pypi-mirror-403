from pathlib import Path
from datetime import datetime, timezone
import json


LOG_FILE = ".devopsmind_exec.log"


def log_execution(workspace: str | Path, command: str, return_code: int):
    """
    Append a command execution record.

    Guarantees:
    - Append-only
    - Deterministic
    - UTC timestamps
    - Validator-safe (no side effects)
    """

    workspace = Path(workspace)
    log_path = workspace / LOG_FILE

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "return_code": return_code,
    }

    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    import sys

    if len(sys.argv) != 4:
        return

    workspace = sys.argv[1]
    command = sys.argv[2]
    try:
        rc = int(sys.argv[3])
    except ValueError:
        rc = -1

    log_execution(workspace, command, rc)


if __name__ == "__main__":
    main()
