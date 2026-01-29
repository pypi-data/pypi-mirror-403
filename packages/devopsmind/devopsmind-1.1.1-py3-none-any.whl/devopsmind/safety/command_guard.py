import sys
import json
from pathlib import Path

from devopsmind.safety.stack_policy import (
    is_command_blocked,
    apply_lab_overrides,
)


def main():
    """
    DevOpsMind command guard.

    argv:
      1 -> stack
      2 -> workspace
      3 -> raw command
      4 -> overrides json path (optional)
    """

    if len(sys.argv) < 4:
        sys.exit(0)

    stack = sys.argv[1]
    workspace = Path(sys.argv[2])
    command = sys.argv[3]
    overrides_path = sys.argv[4] if len(sys.argv) > 4 else ""

    # -------------------------------------------------
    # Load per-lab overrides
    # -------------------------------------------------
    overrides = {}
    if overrides_path:
        try:
            overrides = json.loads(Path(overrides_path).read_text())
        except Exception:
            overrides = {}

    # -------------------------------------------------
    # Lab-specific overrides FIRST
    # -------------------------------------------------
    blocked, reason = apply_lab_overrides(command, overrides)
    if blocked:
        print("✖ Command blocked by lab safety policy")
        print(f"ℹ Reason: {reason}")
        sys.exit(1)

    # -------------------------------------------------
    # Global + stack policy
    # -------------------------------------------------
    blocked, reason = is_command_blocked(command, stack)
    if blocked:
        print("✖ Command blocked by DevOpsMind safety policy")
        print(f"ℹ Reason: {reason}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
