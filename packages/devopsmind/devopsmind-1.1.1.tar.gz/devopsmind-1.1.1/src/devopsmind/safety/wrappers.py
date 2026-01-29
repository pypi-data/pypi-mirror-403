import tempfile
from pathlib import Path

WRAPPER_TEMPLATE = """#!/usr/bin/env python3
from devopsmind.safety.wrapper_common import run_wrapper
run_wrapper("{tool}", "{binary}")
"""

TOOLS = {
    "terraform": "terraform",
    "docker": "docker",
    "kubectl": "kubectl",
    "aws": "aws",
    "helm": "helm",
}


def create_safe_wrappers() -> Path:
    """
    Creates a temporary directory containing safe wrapper binaries.
    Returned path must be prepended to PATH.
    """
    tmp = Path(tempfile.mkdtemp(prefix="devopsmind-safe-bin-"))

    for tool, binary in TOOLS.items():
        wrapper = tmp / tool
        wrapper.write_text(
            WRAPPER_TEMPLATE.format(tool=tool, binary=binary)
        )
        wrapper.chmod(0o755)

    return tmp
