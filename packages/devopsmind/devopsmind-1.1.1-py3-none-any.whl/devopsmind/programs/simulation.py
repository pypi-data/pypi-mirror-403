# src/devopsmind/programs/simulation.py

from pathlib import Path
from devopsmind.programs.core.rule_loader import load_program_module


def simulate_program(
    program: str,
    workspace: Path,
) -> dict:
    """
    Provide a guided simulation context for a program.

    BuildTrack simulation:
    - logical only
    - no execution
    - no pass/fail
    - no gating
    """

    rules_module = load_program_module(program, "simulation_rules")

    # Program may optionally define simulation guidance
    if not hasattr(rules_module, "SIMULATION_CONTEXT"):
        return {
            "summary": (
                "This program focuses on design-first learning.\n"
                "Use the workspace to capture your thinking and create declarative artifacts."
            ),
            "focus": [
                "Write design intent in DESIGN.md files",
                "Use README.md to understand what to create",
                "Create real tool files to practice syntax",
            ],
            "next_steps": [
                "Start with execution/docker",
                "Describe intent before writing files",
                "Run validation as you make progress",
            ],
        }

    context = rules_module.SIMULATION_CONTEXT

    # Workspace-aware hints (non-blocking, optional)
    hints = []
    for folder in context.get("expected_folders", []):
        if not (workspace / folder).exists():
            hints.append(
                f"Consider creating `{folder}` to capture design for this responsibility."
            )

    return {
        "summary": context.get(
            "summary",
            "This program provides guided design practice.",
        ),
        "focus": context.get("focus", []),
        "next_steps": context.get("next_steps", []),
        "hints": hints,
    }
