# src/devopsmind/runtime/program_container.py

from pathlib import Path
import subprocess
import uuid

RUNTIME_IMAGE_PREFIX = "infraforgelabs/devopsmind-runtime"

# Workspace visible inside container (learner-owned)
WORKSPACE_CONTAINER_ROOT = "/workspace"

# Engine-owned program data (missions, preload, validators)
PROGRAM_CONTAINER_ROOT = "/program"

# Runtime-only secret state (tmpfs)
RUNTIME_STATE_ROOT = "/var/lib/devopsmind"


def generate_session_id() -> str:
    """
    Generate a short, unique session ID.
    """
    return uuid.uuid4().hex[:8]


def start_program_container(
    program_name: str,
    workspace: Path,
    program_source: Path,
    session_id: str | None = None,
) -> str:
    """
    Start an isolated per-program container.

    - Workspace is bind-mounted (learner-owned, writable)
    - Program source is bind-mounted read-only (engine-owned)
    - Runtime state uses tmpfs (container-only, non-persistent)
    - Container is removed automatically on exit

    Returns:
        container_name (str)

    Raises:
        RuntimeError if container fails to start
    """

    workspace = workspace.resolve()
    program_source = program_source.resolve()

    if not workspace.exists():
        raise RuntimeError(f"Workspace does not exist: {workspace}")

    if not program_source.exists():
        raise RuntimeError(f"Program source does not exist: {program_source}")

    # -------------------------------------------------
    # Session / container naming
    # -------------------------------------------------
    if not session_id:
        session_id = generate_session_id()

    container_name = f"devopsmind-program-{program_name}-{session_id}"

    # -------------------------------------------------
    # Runtime image (validated earlier)
    # -------------------------------------------------
    runtime_version_file = Path.home() / ".devopsmind" / "runtime_version"
    if not runtime_version_file.exists():
        raise RuntimeError("DevOpsMind runtime is not initialized")

    runtime_version = runtime_version_file.read_text().strip()
    runtime_image = f"{RUNTIME_IMAGE_PREFIX}:{runtime_version}"

    # -------------------------------------------------
    # Ensure no stale container exists
    # -------------------------------------------------
    subprocess.run(
        ["docker", "rm", "-f", "-v", container_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # -------------------------------------------------
    # Start container
    # -------------------------------------------------
    cmd = [
        "docker",
        "run",
        "-d",
        "--name",
        container_name,
        "--hostname",
        program_name,

        # Labels (cleanup / debugging)
        "--label",
        f"devopsmind.program={program_name}",
        "--label",
        f"devopsmind.session={session_id}",

        # Workspace (learner-owned)
        "-v",
        f"{workspace}:{WORKSPACE_CONTAINER_ROOT}",

        # Program source (engine-owned, read-only)
        "-v",
        f"{program_source}:{PROGRAM_CONTAINER_ROOT}:ro",

        # 🔒 Runtime-only secret storage
        "--tmpfs",
        f"{RUNTIME_STATE_ROOT}:rw,noexec,nosuid,size=16m",

        "-w",
        WORKSPACE_CONTAINER_ROOT,

        runtime_image,
        "sleep",
        "infinity",
    ]

    try:
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to start program container:\n{e.stderr}"
        ) from e

    return container_name
