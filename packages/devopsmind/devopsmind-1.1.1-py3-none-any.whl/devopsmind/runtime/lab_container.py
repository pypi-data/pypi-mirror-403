from pathlib import Path
import subprocess
import uuid


RUNTIME_IMAGE_PREFIX = "infraforgelabs/devopsmind-runtime"
WORKSPACE_CONTAINER_ROOT = "/workspace"

# 👇 Engine-owned lab files (env/, validator, metadata)
CHALLENGE_CONTAINER_ROOT = "/lab"

# 👇 Runtime-only secret state (tmpfs)
RUNTIME_STATE_ROOT = "/var/lib/devopsmind"


def generate_session_id() -> str:
    """
    Generate a short, unique session ID.

    Kept for backward compatibility with existing imports.
    """
    return uuid.uuid4().hex[:8]


def start_lab_container(
    lab_id: str,
    workspace: Path,
    lab_source: Path,   # engine-owned lab definition
    session_id: str | None = None,
) -> str:
    """
    Start an isolated per-lab container.

    - Workspace is bind-mounted (learner-owned, writable)
    - Lab source is bind-mounted read-only (engine-owned)
    - Runtime state uses tmpfs (container-only, non-persistent)
    - Container is removed automatically on exit

    Returns:
        container_name (str)

    Raises:
        RuntimeError if container fails to start
    """

    workspace = workspace.resolve()
    lab_source = lab_source.resolve()

    if not workspace.exists():
        raise RuntimeError(f"Workspace does not exist: {workspace}")

    if not lab_source.exists():
        raise RuntimeError(
            f"Lab source does not exist: {lab_source}"
        )

    # -------------------------------------------------
    # Session / container naming
    # -------------------------------------------------
    if not session_id:
        session_id = generate_session_id()

    container_name = f"devopsmind-lab-{lab_id}-{session_id}"

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
        lab_id,

        # Labels (cleanup / debugging)
        "--label",
        f"devopsmind.lab={lab_id}",
        "--label",
        f"devopsmind.session={session_id}",

        # Workspace (learner-owned)
        "-v",
        f"{workspace}:{WORKSPACE_CONTAINER_ROOT}",

        # Lab source (engine-owned, read-only)
        "-v",
        f"{lab_source}:{CHALLENGE_CONTAINER_ROOT}:ro",

        # 🔒 Runtime-only secret storage (FIX)
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
            f"Failed to start lab container:\n{e.stderr}"
        ) from e

    return container_name
