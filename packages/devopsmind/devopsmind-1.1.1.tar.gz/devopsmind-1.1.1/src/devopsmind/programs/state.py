# src/devopsmind/programs/state.py

import json
from pathlib import Path

from devopsmind.programs.progress import load_progress

# ------------------------------------------------------------
# Program State Location (LOCKED)
# ------------------------------------------------------------

STATE_ROOT = Path.home() / ".devopsmind" / "programs"

# ------------------------------------------------------------
# Default Program State
# ------------------------------------------------------------

DEFAULT_STATE = {
    "systems": {
        "execution": "LOCKED",
        "resilience": "LOCKED",
        "delivery": "LOCKED",
    }
}

# ------------------------------------------------------------
# Valid State Machine (LOCKED)
# ------------------------------------------------------------

VALID_ORDER = ["execution", "resilience", "delivery"]
VALID_STATES = ["LOCKED", "IN_PROGRESS", "STABILIZED"]

# ------------------------------------------------------------
# Core State IO
# ------------------------------------------------------------

def load_program_state(program_id: str) -> dict:
    state_file = _state_file(program_id)

    if not state_file.exists():
        save_program_state(program_id, DEFAULT_STATE)
        return DEFAULT_STATE.copy()

    with state_file.open() as f:
        return json.load(f)


def save_program_state(program_id: str, state: dict) -> None:
    state_file = _state_file(program_id)
    state_file.parent.mkdir(parents=True, exist_ok=True)

    with state_file.open("w") as f:
        json.dump(state, f, indent=2)


def _state_file(program_id: str) -> Path:
    return STATE_ROOT / program_id / "program_state.json"

# ------------------------------------------------------------
# Transition Rules (Internal Only)
# ------------------------------------------------------------

def can_transition(state: dict, system: str, target: str) -> bool:
    systems = state.get("systems", {})

    if system not in systems:
        return False

    if system not in VALID_ORDER or target not in VALID_STATES:
        return False

    current = systems[system]

    if VALID_STATES.index(target) != VALID_STATES.index(current) + 1:
        return False

    system_index = VALID_ORDER.index(system)
    if system_index > 0:
        previous_system = VALID_ORDER[system_index - 1]
        if systems.get(previous_system) != "STABILIZED":
            return False

    return True


def transition_system(state: dict, system: str, target: str) -> dict:
    if not can_transition(state, system, target):
        raise ValueError("Invalid system transition")

    state["systems"][system] = target
    return state

# ------------------------------------------------------------
# Internal Transition Hooks
# ------------------------------------------------------------

def mark_system_started(program_id: str, system: str) -> dict:
    state = load_program_state(program_id)

    if can_transition(state, system, "IN_PROGRESS"):
        state = transition_system(state, system, "IN_PROGRESS")
        save_program_state(program_id, state)

    return state


def mark_system_completed(program_id: str, system: str) -> dict:
    state = load_program_state(program_id)

    if can_transition(state, system, "STABILIZED"):
        state = transition_system(state, system, "STABILIZED")
        save_program_state(program_id, state)

    return state

# ------------------------------------------------------------
# AUTO-STABILIZE (GUARDED BY PROGRESS)
# ------------------------------------------------------------

def auto_stabilize_if_ready(program_id: str, system: str) -> None:
    """
    Stabilize a system ONLY if:
    - it is IN_PROGRESS
    - transition rules allow it
    - progress for the system is > 0
    """
    state = load_program_state(program_id)
    current = state.get("systems", {}).get(system)

    if current != "IN_PROGRESS":
        return

    progress = load_progress(program_id)
    system_progress = progress.get("systems", {}).get(system, 0)

    # HARD GUARD: no progress, no stabilization
    if system_progress <= 0:
        return

    if can_transition(state, system, "STABILIZED"):
        state = transition_system(state, system, "STABILIZED")
        save_program_state(program_id, state)
