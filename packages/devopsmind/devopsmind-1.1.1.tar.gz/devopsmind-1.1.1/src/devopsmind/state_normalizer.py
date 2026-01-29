# XP INVARIANT (LOCKED)
# - xp.labs     → drives rank & role progress
# - xp.projects → capstone effort only
# - xp.total    → labs + projects (display & snapshot)
# - Rank must NEVER use xp.total

import copy

# -------------------------------------------------
# 🔹 Tier state normalization (PURE, ADDITIVE)
# -------------------------------------------------
def _ensure_tier_state(state: dict) -> dict:
    state = copy.deepcopy(state)

    tiers = state.setdefault("tiers", {})
    owned = tiers.setdefault("owned", [])

    if "foundation_core" not in owned:
        owned.append("foundation_core")

    return state


# -------------------------------------------------
# 🔹 Update metadata normalization (PURE)
# -------------------------------------------------
def _ensure_update_state(state: dict) -> dict:
    state = copy.deepcopy(state)
    state.setdefault("available_update", None)
    return state


# -------------------------------------------------
# 🔥 Streak state normalization (PURE, ADDITIVE)
# -------------------------------------------------
def _ensure_streak_state(state: dict) -> dict:
    state = copy.deepcopy(state)

    state.setdefault("streak_days", 0)
    state.setdefault("last_active_date", None)
    state.setdefault("streak_broken_on", None)
    state.setdefault("streak_notified", True)
    state.setdefault("mentor_nudges_seen", [])

    return state


# -------------------------------------------------
# 🧠 XP normalization (CRITICAL)
# -------------------------------------------------
def _ensure_xp_state(state: dict) -> dict:
    """
    Normalize XP schema.

    LEGACY:
      "xp": 3200

    NEW (LOCKED):
      "xp": {
        "labs": 3200,
        "projects": 0,
        "total": 3200
      }

    HARD RULES:
    - Never lose XP
    - Labs XP remains authoritative
    - Total XP = labs + projects (derived, deterministic)
    """
    state = copy.deepcopy(state)

    xp = state.get("xp", 0)

    # -----------------------------
    # Legacy scalar XP
    # -----------------------------
    if isinstance(xp, int):
        labs = xp
        projects = 0

    # -----------------------------
    # Dict XP (current / future)
    # -----------------------------
    elif isinstance(xp, dict):
        labs = int(xp.get("labs", 0))
        projects = int(xp.get("projects", 0))

    else:
        labs = 0
        projects = 0

    # -----------------------------
    # Enforce canonical structure
    # -----------------------------
    state["xp"] = {
        "labs": labs,
        "projects": projects,
        "total": labs + projects,
    }

    return state


# -------------------------------------------------
# 📦 Project lifecycle normalization (PURE, ADDITIVE)
# -------------------------------------------------
def _ensure_project_state(state: dict) -> dict:
    """
    Ensure project lifecycle container exists.

    Structure (LOCKED):
      "projects": {
        "<project_id>": "not-started | in-progress | validated | completed"
      }
    """
    state = copy.deepcopy(state)
    state.setdefault("projects", {})
    return state


# -------------------------------------------------
# 📈 Progress normalization (CRITICAL)
# -------------------------------------------------
def _ensure_progress_state(state: dict) -> dict:
    """
    Ensure lab progress schema exists.

    Structure (LOCKED):
      "progress": {
        "completed": [],
        "by_stack": {},
        "by_difficulty": {},
        "by_stack_difficulty": {}
      }
    """
    state = copy.deepcopy(state)

    progress = state.setdefault("progress", {})
    progress.setdefault("completed", [])
    progress.setdefault("by_stack", {})
    progress.setdefault("by_difficulty", {})
    progress.setdefault("by_stack_difficulty", {})

    return state


# -------------------------------------------------
# 🧩 by_stack_difficulty normalization (PURE)
# -------------------------------------------------
def _ensure_by_stack_difficulty_state(state: dict) -> dict:
    state = copy.deepcopy(state)

    progress = state.setdefault("progress", {})
    by_sd = progress.setdefault("by_stack_difficulty", {})
    by_diff = progress.get("by_difficulty", {})

    if "__legacy__" in by_sd:
        return state

    if by_diff:
        legacy = {k: v for k, v in by_diff.items() if v > 0}
        if legacy:
            by_sd["__legacy__"] = legacy

    return state


# -------------------------------------------------
# 🔒 MASTER NORMALIZER
# -------------------------------------------------
def normalize_state(state: dict) -> dict:
    """
    Apply ALL schema upgrades in a pure, deterministic way.

    HARD RULES:
    - STRUCTURE ONLY
    - NO progression mutation
    - NO XP loss
    """
    state = _ensure_tier_state(state)
    state = _ensure_update_state(state)
    state = _ensure_streak_state(state)
    state = _ensure_xp_state(state)
    state = _ensure_project_state(state)
    state = _ensure_progress_state(state)          # ✅ REQUIRED
    state = _ensure_by_stack_difficulty_state(state)
    return state
