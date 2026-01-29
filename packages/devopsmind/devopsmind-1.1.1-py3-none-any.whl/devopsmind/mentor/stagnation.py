# src/devopsmind/mentor/stagnation.py

from devopsmind.state import load_state, save_state
from devopsmind.constants import DIFFICULTY_LADDER

STUCK_THRESHOLD = 3  # attempts before gentle intervention


def _difficulty_band(difficulty: str) -> str:
    """
    Map difficulty to a conceptual band.
    Uses canonical DIFFICULTY_LADDER ordering.
    """
    if difficulty not in DIFFICULTY_LADDER:
        return "advanced"

    idx = DIFFICULTY_LADDER.index(difficulty)

    if idx <= 0:          # Easy
        return "foundation"
    if idx <= 2:          # Medium, Hard
        return "growth"
    if idx <= 4:          # Expert, Master
        return "advanced"
    return "leadership"   # Architect+


def _motivational_message(difficulty: str, attempts: int) -> str:
    band = _difficulty_band(difficulty)

    if band == "foundation":
        return (
            "You’ve shown persistence here, which is exactly how foundations form. "
            "This is a good moment to slow down and revisit the core mechanics "
            "the lab is testing."
        )

    if band == "growth":
        return (
            "This lab sits in a growth zone where progress often comes "
            "after stepping back. Strengthening nearby concepts now will make "
            "your next attempt feel lighter."
        )

    if band == "advanced":
        return (
            "At this level, friction is expected. These labs reward pattern "
            "recognition more than repetition. Building supporting intuition "
            "will pay off quickly when you return."
        )

    # leadership band (Architect → Fellow)
    return (
        "Labs at this level are intentionally resistant. "
        "Time spent reflecting, modeling trade-offs, or reviewing adjacent systems "
        "is not delay — it’s part of the work."
    )


def detect_stagnation_once():
    """
    Detect if the user is stuck on a lab.
    This message is shown ONLY ONCE per lab.
    """

    state = load_state()

    failures = state.get("validation_failures", {})
    completed = set(state.get("progress", {}).get("completed", []))

    mentor_state = state.setdefault("mentor", {})
    shown = mentor_state.setdefault("stagnation_shown", {})

    difficulties = state.get("lab_difficulties", {})

    for lab_id, attempts in failures.items():
        if attempts < STUCK_THRESHOLD:
            continue

        if lab_id in completed:
            continue

        if shown.get(lab_id):
            continue

        difficulty = difficulties.get(lab_id)
        message = _motivational_message(difficulty, attempts)

        shown[lab_id] = True
        save_state(state)

        return {
            "lab_id": lab_id,
            "attempts": attempts,
            "difficulty": difficulty,
            "message": message,
        }

    return None
