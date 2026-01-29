"""
DevOpsMind Lab Linter

Purpose:
- Author-side structural & philosophy validation
- Non-blocking, advisory-only
- Used by `devopsmind doctor`

Core Rules (LOCKED):
- Users MAY run commands
- Validators MUST remain static by default
- Execution context is ALWAYS declared
- Execution proof is OPTIONAL and DECLARED
- Validators MUST NOT execute tools
  (EXCEPT Git discovery labs)

Philosophy:
Free · Local · User-Owned · Skill-First · Judgment-Driven
"""

from pathlib import Path
import yaml
import re

from devopsmind.constants import DIFFICULTY_LADDER


# =================================================
# Canonical platform contracts (LOCKED)
# =================================================

KNOWN_STACKS = {
    "linux", "git", "docker", "kubernetes", "helm",
    "terraform", "ansible", "jenkins", "argocd",
    "aws", "azure", "gcp",
    "networking", "observability",
    "python", "aiops",
}

HARD_TIERS = {
    "Hard", "Expert", "Master",
    "Architect", "Principal",
    "Staff", "Distinguished", "Fellow",
}

# 🔒 LOCKED: DevOpsMind runtime is ALWAYS Docker
ALLOWED_RUNTIMES = {"docker"}

GIT_MODES = {"discovery", "transformation"}


# =================================================
# Public API
# =================================================

def lint_lab(lab_dir: Path) -> list[str]:
    raw_errors: list[str] = []

    if not lab_dir.exists():
        return []

    lab_yaml = lab_dir / "lab.yaml"

    # -------------------------------------------------
    # Core presence
    # -------------------------------------------------

    if not lab_yaml.exists():
        raw_errors.append("Missing lab.yaml")
        return _box_errors(raw_errors)

    meta = _load_yaml(lab_yaml, raw_errors)
    if meta is None:
        return _box_errors(raw_errors)

    difficulty = meta.get("difficulty", "Easy")
    stack = str(meta.get("stack", "")).lower()
    git_mode = meta.get("git_mode")

    # -------------------------------------------------
    # Difficulty validity
    # -------------------------------------------------

    if difficulty not in DIFFICULTY_LADDER:
        raw_errors.append(
            f"Invalid difficulty level\n"
            f"Found: {difficulty}\n"
            f"Expected: {DIFFICULTY_LADDER}"
        )

    # -------------------------------------------------
    # Stack validity (advisory)
    # -------------------------------------------------

    if stack and stack not in KNOWN_STACKS:
        raw_errors.append(
            "Unknown stack identifier (advisory)\n"
            f"Found: {stack}\n"
            f"Expected one of: {sorted(KNOWN_STACKS)}"
        )

    # -------------------------------------------------
    # Git-specific contract
    # -------------------------------------------------

    if stack == "git":
        if git_mode not in GIT_MODES:
            raw_errors.append(
                "Missing or invalid git_mode\n"
                "Git labs must declare git_mode: discovery | transformation"
            )

    # -------------------------------------------------
    # Required metadata fields
    # -------------------------------------------------

    _require_fields(
        meta,
        required=[
            "id",
            "title",
            "stack",
            "difficulty",
            "xp",
            "goal",
            "skills",
            "validator",
            "execution",
        ],
        errors=raw_errors,
    )

    # -------------------------------------------------
    # Solution awareness (Hard+ advisory — ALWAYS VISIBLE)
    # -------------------------------------------------

    if difficulty in HARD_TIERS and "solution" not in meta:
        raw_errors.append(
            "Missing solution walkthrough (advisory)\n"
            "Hard+ labs should explain real-world intent"
        )

    # -------------------------------------------------
    # 🔒 Execution semantics (HARD RULE)
    # -------------------------------------------------

    execution = meta.get("execution")

    if not isinstance(execution, dict):
        raw_errors.append(
            "Invalid execution block\n"
            "Execution must define runtime and requires_execution"
        )
    else:
        runtime = execution.get("runtime")
        requires_exec = execution.get("requires_execution")

        # 🚨 HARD ENFORCEMENT: Docker only
        if runtime != "docker":
            raw_errors.append(
                "Invalid execution runtime (HARD RULE)\n"
                f"Found: {runtime}\n"
                "DevOpsMind requires:\n"
                "execution:\n"
                "  runtime: docker"
            )

        if not isinstance(requires_exec, bool):
            raw_errors.append(
                "Invalid execution.requires_execution\n"
                "Must be boolean true/false"
            )

    # -------------------------------------------------
    # Validator checks (DEFENSIVE)
    # -------------------------------------------------

    validator_ref = meta.get("validator", "")
    validator_path = lab_dir / validator_ref

    if not validator_path.exists():
        raw_errors.append("Validator file missing")
    elif not validator_path.is_file():
        raw_errors.append("Validator path is not a file")
    else:
        validator_code = validator_path.read_text()

        _lint_validator_contract(
            validator_code,
            raw_errors,
            stack=stack,
            git_mode=git_mode
        )

    return _box_errors(raw_errors)


# =================================================
# Helpers
# =================================================

def _lint_validator_contract(code: str, errors: list[str], *, stack: str, git_mode: str):
    if "def validate" not in code:
        errors.append("Validator missing validate() function")

    # Subprocess rules
    if "subprocess." in code:
        if not (stack == "git" and git_mode == "discovery"):
            errors.append(
                "Forbidden operation in validator\n"
                "Found: subprocess.\n"
                "Subprocess is only allowed for Git discovery labs."
            )

    if "return True," not in code:
        errors.append("Validator must return (bool, message)")
    if "return False," not in code:
        errors.append("Validator must return (bool, message)")


def _box_errors(errors: list[str]) -> list[str]:
    boxed = []
    for idx, err in enumerate(errors, start=1):
        lines = err.splitlines()
        width = max(len(line) for line in lines) + 4
        top = "┌" + "─" * (width - 2) + "┐"
        bottom = "└" + "─" * (width - 2) + "┘"
        body = [f"│ {line.ljust(width - 4)} │" for line in lines]
        boxed.append("\n".join(
            [top] +
            [f"│ Issue {idx}".ljust(width - 1) + "│"] +
            body +
            [bottom]
        ))
    return boxed


def _load_yaml(path: Path, errors: list[str]) -> dict | None:
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception as e:
        errors.append(f"Invalid YAML\n{e}")
        return None


def _require_fields(data: dict, required: list, errors: list[str]):
    for field in required:
        if field not in data:
            errors.append(f"Missing required field\n{field}")
