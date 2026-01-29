import subprocess
import os

from devopsmind.safety.workspace import ensure_inside_workspace
from devopsmind.safety.stack_policy import is_command_blocked


def safe_run(cmd, *args, **kwargs):
    """
    Drop-in replacement for subprocess.run
    """

    dev_mode = os.environ.get("DEVOPSMIND_DEV") == "1"
    validator_mode = os.environ.get("DEVOPSMIND_VALIDATOR") == "1"

    # 🔒 Enforce workspace confinement ONLY for user commands
    if not (dev_mode or validator_mode):
        ensure_inside_workspace()

    if isinstance(cmd, (list, tuple)):
        cmd_str = " ".join(cmd)
        tool = cmd[0]
    else:
        cmd_str = str(cmd)
        tool = cmd_str.split()[0]

    # ✅ Centralized policy enforcement
    blocked, reason = is_command_blocked(cmd_str, stack=tool)
    if blocked:
        raise RuntimeError(reason)

    return subprocess._original_run(cmd, *args, **kwargs)
