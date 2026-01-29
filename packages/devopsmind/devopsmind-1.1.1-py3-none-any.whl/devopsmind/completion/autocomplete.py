from pathlib import Path
import os
import re

from .generator import generate_all, COMPLETION_VERSION

# -------------------------------------------------
# Paths
# -------------------------------------------------

DEVOPSMIND_DIR = Path.home() / ".devopsmind"

BASH_FILE = DEVOPSMIND_DIR / "devopsmind.bash"
ZSH_FILE = DEVOPSMIND_DIR / "devopsmind.zsh"

BASH_RC_FILES = [
    Path.home() / ".bashrc",
    Path.home() / ".bash_profile",
]

ZSH_RC_FILE = Path.home() / ".zshrc"

SOURCE_LINE_BASH = "source ~/.devopsmind/devopsmind.bash"
SOURCE_LINE_ZSH = "source ~/.devopsmind/devopsmind.zsh"

VERSION_PATTERN = re.compile(r"DEVOPSMIND_COMPLETION_VERSION=(\d+)")


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def _detect_shell() -> str | None:
    shell = os.environ.get("SHELL", "")
    if shell.endswith("bash"):
        return "bash"
    if shell.endswith("zsh"):
        return "zsh"
    return None


def _read_version(path: Path) -> int | None:
    if not path.exists():
        return None

    try:
        for line in path.read_text().splitlines():
            match = VERSION_PATTERN.search(line)
            if match:
                return int(match.group(1))
    except Exception:
        pass

    return None


def _ensure_sourced(rc_file: Path, source_line: str):
    if not rc_file.exists():
        return

    content = rc_file.read_text()
    if source_line in content:
        return

    with rc_file.open("a") as f:
        f.write(f"\n# DevOpsMind autocomplete\n{source_line}\n")


# -------------------------------------------------
# Public API
# -------------------------------------------------

def ensure_installed():
    """
    Version-aware, idempotent autocomplete installer.
    Safe to call on every CLI invocation.
    """

    shell = _detect_shell()
    if not shell:
        return

    DEVOPSMIND_DIR.mkdir(parents=True, exist_ok=True)

    # Determine target file
    target_file = BASH_FILE if shell == "bash" else ZSH_FILE

    existing_version = _read_version(target_file)

    # Regenerate ONLY if version differs
    if existing_version != COMPLETION_VERSION:
        generate_all(DEVOPSMIND_DIR)

    # Ensure sourcing
    if shell == "bash":
        for rc in BASH_RC_FILES:
            _ensure_sourced(rc, SOURCE_LINE_BASH)

    elif shell == "zsh":
        _ensure_sourced(ZSH_RC_FILE, SOURCE_LINE_ZSH)
