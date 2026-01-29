# devopsmind/safety/preflight.py

import platform
import shutil
from typing import Dict, List, Tuple


# -------------------------------------------------
# Dependency registry (AUTHORITATIVE)
# -------------------------------------------------
DEPENDENCIES: Dict[str, Dict[str, str]] = {
    "docker": {
        "binary": "docker",
        "linux": "https://docs.docker.com/get-docker/",
        "darwin": "https://docs.docker.com/desktop/install/mac-install/",
        "windows": "https://docs.docker.com/desktop/install/windows-install/",
    },
    "kubectl": {
        "binary": "kubectl",
        "linux": "https://kubernetes.io/docs/tasks/tools/",
        "darwin": "https://kubernetes.io/docs/tasks/tools/",
        "windows": "https://kubernetes.io/docs/tasks/tools/",
    },
    "helm": {
        "binary": "helm",
        "linux": "https://helm.sh/docs/intro/install/",
        "darwin": "https://helm.sh/docs/intro/install/",
        "windows": "https://helm.sh/docs/intro/install/",
    },
    "terraform": {
        "binary": "terraform",
        "linux": "https://developer.hashicorp.com/terraform/install",
        "darwin": "https://developer.hashicorp.com/terraform/install",
        "windows": "https://developer.hashicorp.com/terraform/install",
    },
    "ansible": {
        "binary": "ansible-playbook",
        "linux": "https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html",
        "darwin": "https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html",
        "windows": "https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html",
    },
}


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _platform_key() -> str:
    system = platform.system()
    if system == "Linux":
        return "linux"
    if system == "Darwin":
        return "darwin"
    return "windows"


def _is_available(binary: str) -> bool:
    return shutil.which(binary) is not None


# -------------------------------------------------
# Public API
# -------------------------------------------------
def check_dependencies(
    required: List[str],
    runtime: str,
) -> Tuple[bool, str]:
    """
    Runtime-aware dependency check.

    Rules:
    - docker runtime  -> only Docker is required on host
    - native runtime  -> all required tools must exist on host

    Returns:
      (ok, message)
    """

    # -----------------------------
    # Docker runtime: host needs Docker ONLY
    # -----------------------------
    if runtime == "docker":
        if not _is_available("docker"):
            os_key = _platform_key()
            meta = DEPENDENCIES["docker"]
            url = meta.get(os_key) or meta.get("linux")

            return (
                False,
                "\n".join(
                    [
                        "❌ Cannot start lab",
                        "",
                        "Docker is required but not found.",
                        "",
                        f"Install Docker: {url}",
                        "",
                        "Docker is used to provide all required tools safely.",
                    ]
                ),
            )

        return True, ""

    # -----------------------------
    # Native runtime: strict host checks
    # -----------------------------
    if not required:
        return True, ""

    missing = []

    for dep in required:
        meta = DEPENDENCIES.get(dep)
        if not meta:
            continue  # forward-compatible

        if not _is_available(meta["binary"]):
            missing.append(dep)

    if not missing:
        return True, ""

    os_key = _platform_key()

    lines = [
        "❌ Cannot start lab",
        "",
        "Missing required tools:",
    ]

    for dep in missing:
        meta = DEPENDENCIES[dep]
        url = meta.get(os_key) or meta.get("linux")
        lines.append(f"  - {dep}")
        lines.append(f"    Install: {url}")

    lines.append("")
    lines.append("Tip: run `devopsmind doctor` to verify your system.")

    return False, "\n".join(lines)
