# devopsmind/safety/docker_check.py

import shutil


def docker_available() -> bool:
    """
    Returns True if docker CLI is available.
    """
    return shutil.which("docker") is not None


def docker_compose_available() -> bool:
    """
    Returns True if docker compose is available.
    Supports both:
      - docker compose (plugin)
      - docker-compose (legacy)
    """
    if shutil.which("docker-compose"):
        return True

    docker = shutil.which("docker")
    if not docker:
        return False

    # docker compose plugin
    try:
        import subprocess
        subprocess.run(
            ["docker", "compose", "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except Exception:
        return False
