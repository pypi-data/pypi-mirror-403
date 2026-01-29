from pathlib import Path
import subprocess

from devopsmind.progress import load_state, save_state


def run_env_and_capture_secrets(
    *,
    lab_id: str,
    container_name: str,
    lab_source: Path,
    workspace: Path,
    execution: dict,
) -> tuple[bool, str | None]:
    """
    Handles full environment lifecycle for a lab:

    - Checks requires_execution flag
    - Executes env/env.py inside container
    - Captures DEVOPSMIND_* secrets from stdout
    - Persists secrets into engine state
    - Ensures idempotency via .devopsmind_env_done

    Returns:
        (success: bool, error_message: str | None)
    """

    # -------------------------------------------------
    # Should this lab execute env at all?
    # -------------------------------------------------
    requires_exec = execution.get("requires_execution", False)
    if not requires_exec:
        return True, None

    env_script = lab_source / "env" / "env.py"
    env_marker = workspace / ".devopsmind_env_done"

    # -------------------------------------------------
    # Idempotency guard
    # -------------------------------------------------
    if not env_script.exists() or env_marker.exists():
        return True, None

    # -------------------------------------------------
    # Execute env script inside container
    # -------------------------------------------------
    result = subprocess.run(
        [
            "docker",
            "exec",
            container_name,
            "python3",
            "/lab/env/env.py",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        return False, result.stderr or "env/env.py execution failed"

    # -------------------------------------------------
    # 🔒 Capture DEVOPSMIND_* secrets (GENERIC)
    # -------------------------------------------------
    secrets = {}

    for line in (result.stdout or "").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            if k.startswith("DEVOPSMIND_"):
                secrets[k] = v

    if secrets:
        state = load_state()
        lab_secrets = state.setdefault("lab_secrets", {})
        lab_secrets[lab_id] = secrets
        save_state(state)

    # -------------------------------------------------
    # Mark env execution complete
    # -------------------------------------------------
    env_marker.write_text("done")

    return True, None
