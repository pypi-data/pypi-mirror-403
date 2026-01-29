import json
from pathlib import Path

from .constants import DATA_DIR
from .state_normalizer import normalize_state

STATE_FILE = DATA_DIR / "state.json"


def _sync_total_xp(state: dict):
    """
    Ensure total XP is always consistent.

    HARD RULE:
    total = labs + projects
    """
    xp = state.get("xp", {})
    labs = int(xp.get("labs", 0))
    projects = int(xp.get("projects", 0))
    xp["total"] = labs + projects
    state["xp"] = xp


def load_state():
    if not STATE_FILE.exists():
        state = {
            "profile": {},
            "xp": {
                "labs": 0,
                "projects": 0,
                "total": 0,
            },

            # 📦 Project lifecycle state (LOCKED)
            "projects": {},

            "badges": [],
            "achievements_unlocked": [],
            "milestones_awarded": [],
            "progress": {
                "completed": [],
                "by_stack": {},
                "by_difficulty": {},
                "by_stack_difficulty": {},
            },
            "attempts": {},
        }
    else:
        state = json.loads(STATE_FILE.read_text())

    # ---------------------------------------------
    # Normalize legacy schema
    # ---------------------------------------------
    normalized = normalize_state(state)

    # ---------------------------------------------
    # Ensure total XP consistency
    # ---------------------------------------------
    _sync_total_xp(normalized)

    if normalized != state:
        save_state(normalized)

    # ---- Legacy badge migration ----
    if normalized.get("achievements_unlocked") and not normalized.get("badges"):
        normalized["badges"] = list(normalized["achievements_unlocked"])
        save_state(normalized)

    return normalized


def save_state(state):
    _sync_total_xp(state)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def persist_earned_badges(state, earned_badges):
    if not earned_badges:
        return

    badges = set(state.get("badges", []))
    achievements = set(state.get("achievements_unlocked", []))

    for badge_id in earned_badges:
        badges.add(badge_id)
        achievements.add(badge_id)

    state["badges"] = sorted(badges)
    state["achievements_unlocked"] = sorted(achievements)


# -------------------------------------------------
# Lab completion (AUTHORITATIVE)
# -------------------------------------------------
def record_completion(
    lab_id,
    stack=None,
    difficulty=None,
    earned_badges=None,
    lab_xp=0,
):
    state = load_state()
    progress = state["progress"]

    # Idempotent guard
    if lab_id in progress["completed"]:
        return state, 0

    progress["completed"].append(lab_id)

    if stack:
        progress["by_stack"][stack] = progress["by_stack"].get(stack, 0) + 1

    if difficulty:
        progress["by_difficulty"][difficulty] = (
            progress["by_difficulty"].get(difficulty, 0) + 1
        )

        by_sd = progress.setdefault("by_stack_difficulty", {})
        stack_entry = by_sd.setdefault(stack, {})
        stack_entry[difficulty] = stack_entry.get(difficulty, 0) + 1

    # -------------------------------------------------
    # ✅ LAB XP ONLY
    # -------------------------------------------------
    if lab_xp:
        state["xp"]["labs"] += int(lab_xp)

    # -------------------------------------------------
    # 🎯 Milestones (FACTS ONLY)
    # -------------------------------------------------
    from devopsmind.achievements import load_milestones

    awarded = set(state.get("milestones_awarded", []))
    completed_count = len(progress["completed"])

    for milestone in load_milestones():
        if completed_count >= milestone.completed_gte and milestone.id not in awarded:
            awarded.add(milestone.id)

    state["milestones_awarded"] = sorted(awarded)

    persist_earned_badges(state, earned_badges or [])

    save_state(state)
    return state, 0
