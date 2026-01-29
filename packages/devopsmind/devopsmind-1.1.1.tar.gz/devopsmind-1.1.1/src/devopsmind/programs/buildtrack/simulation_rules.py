# src/devopsmind/programs/buildtrack/simulation_rules.py

"""
BuildTrack Simulation Context

This file defines the learning orientation for BuildTrack.
It does not evaluate, validate, or gate progress.
"""

SIMULATION_CONTEXT = {
    "summary": (
        "BuildTrack helps you practice DevOps design thinking\n"
        "using real tools without execution pressure.\n\n"
        "You will focus on understanding responsibilities,\n"
        "writing intent, and expressing designs declaratively."
    ),

    "focus": [
        "Separate design intent (DESIGN.md) from tool configuration",
        "Think in responsibilities, not tools",
        "Practice declarative configuration without execution",
        "Build confidence through guided validation",
    ],

    "next_steps": [
        "Start by opening a DESIGN.md file and writing intent",
        "Read the README.md in each folder to understand expectations",
        "Create tool files gradually based on your design",
        "Run validation often to receive guidance",
    ],

    # Optional gentle hints (never enforced)
    "expected_folders": [
        "execution/docker",
        "resilience/kubernetes",
        "delivery/cicd",
    ],
}
