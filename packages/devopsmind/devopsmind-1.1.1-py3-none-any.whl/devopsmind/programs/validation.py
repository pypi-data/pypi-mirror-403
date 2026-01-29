# src/devopsmind/programs/validation.py

from pathlib import Path
from devopsmind.programs.core.rule_loader import load_program_module


def validate_workspace(
    program: str,
    workspace: Path,
) -> list[dict]:
    """
    Validate a workspace for a given program.

    BuildTrack validation:
    - never fails
    - never blocks
    - returns guidance only
    """

    rules_module = load_program_module(program, "validation_rules")

    if not hasattr(rules_module, "run_validation"):
        return [{
            "level": "info",
            "symbol": "ℹ️",
            "message": "This program does not define validation rules.",
        }]

    return rules_module.run_validation(workspace)
