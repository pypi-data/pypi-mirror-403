from pathlib import Path
import subprocess
import os

from devopsmind.progress import load_state, save_state
from devopsmind.safety.executor import safe_run


def run_validate_env(
    *,
    lab_id: str,
    lab_dir: Path,
) -> dict:
    """
    Runs optional validation env.py, captures DEVOPSMIND_* secrets,
    persists them, and returns env vars to inject.
    """

    injected_env: dict[str, str] = {}

    env_file = lab_dir / "env.py"
    if not env_file.exists():
        return injected_env

    # Patch subprocess.run safely
    if not hasattr(subprocess, "_original_run"):
        subprocess._original_run = subprocess.run
    subprocess.run = safe_run

    try:
        result = safe_run(
            ["python3", str(env_file)],
            capture_output=True,
            text=True,
        )

        for line in (result.stdout or "").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                if k.startswith("DEVOPSMIND_"):
                    injected_env[k] = v

        if injected_env:
            state = load_state()
            secrets = state.setdefault("lab_secrets", {})
            secrets[lab_id] = injected_env
            save_state(state)

    finally:
        subprocess.run = subprocess._original_run

    return injected_env
