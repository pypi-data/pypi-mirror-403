# src/devopsmind/programs/coverage.py

from pathlib import Path
from devopsmind.programs.core.rule_loader import load_program_module


def calculate_coverage(workspace: Path, program: str = "buildtrack") -> dict:
    """
    Calculate coverage for a program workspace.
    """
    rules_module = load_program_module(program, "coverage_rules")
    COVERAGE_RULES = rules_module.COVERAGE_RULES

    coverage = {}

    for stack, paths in COVERAGE_RULES.items():
        present = 0
        for rel in paths:
            if (workspace / rel).exists():
                present += 1

        coverage[stack] = int((present / len(paths)) * 100) if paths else 0

    return coverage
