from pathlib import Path
import subprocess
import uuid

RUNTIME_IMAGE_PREFIX = "infraforgelabs/devopsmind-runtime"

WORKSPACE_CONTAINER_ROOT = "/workspace"
PROJECT_CONTAINER_ROOT = "/project"
RUNTIME_STATE_ROOT = "/var/lib/devopsmind"


def generate_session_id() -> str:
    return uuid.uuid4().hex[:8]


def start_project_container(
    project_id: str,
    workspace: Path,
    project_source: Path,
    session_id: str | None = None,
) -> str:
    """
    Start an isolated per-project container.

    - Workspace is bind-mounted (~/workspace/project/<id>)
    - Project source is read-only
    - Runtime state is tmpfs
    """

    workspace = workspace.resolve()
    project_source = project_source.resolve()

    if not workspace.exists():
        raise RuntimeError(f"Workspace does not exist: {workspace}")

    if not project_source.exists():
        raise RuntimeError(f"Project source does not exist: {project_source}")

    if not session_id:
        session_id = generate_session_id()

    container_name = f"devopsmind-project-{project_id}-{session_id}"

    runtime_version_file = Path.home() / ".devopsmind" / "runtime_version"
    if not runtime_version_file.exists():
        raise RuntimeError("DevOpsMind runtime is not initialized")

    runtime_version = runtime_version_file.read_text().strip()
    runtime_image = f"{RUNTIME_IMAGE_PREFIX}:{runtime_version}"

    subprocess.run(
        ["docker", "rm", "-f", "-v", container_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    cmd = [
        "docker", "run", "-d",
        "--name", container_name,
        "--hostname", project_id,

        "--label", f"devopsmind.project={project_id}",
        "--label", f"devopsmind.session={session_id}",

        "-v", f"{workspace}:{WORKSPACE_CONTAINER_ROOT}",
        "-v", f"{project_source}:{PROJECT_CONTAINER_ROOT}:ro",

        "--tmpfs", f"{RUNTIME_STATE_ROOT}:rw,noexec,nosuid,size=16m",

        "-w", WORKSPACE_CONTAINER_ROOT,
        runtime_image,
        "sleep", "infinity",
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
            f"Failed to start project container:\n{e.stderr}"
        ) from e

    return container_name
