from typing import Optional
import yaml

from .start import prepare
from .validator import validate_only as _validate_only
from devopsmind.stats import stats as _stats
from devopsmind.list.lab_resolver import find_lab_by_id
from devopsmind.state import get_active_username
from devopsmind.progress import load_state, save_state

from devopsmind.safety.preflight import check_dependencies
from devopsmind.runtime.docker_defaults import (
    DEFAULT_DOCKER_SERVICE,
    FALLBACK_SERVICE,
)


# -------------------------------------------------
# Ensure active profile is always loaded
# -------------------------------------------------
def _ensure_profile_loaded():
    return get_active_username()


# -------------------------------------------------
# Start (ENGINE — preparation only)
# -------------------------------------------------
def start(lab_id: Optional[str] = None):
    """
    Prepare a lab and ensure Docker runtime.

    Returns:
      (context, message)
    """
    _ensure_profile_loaded()

    if not lab_id:
        return None, "Please provide a lab id."

    lab_dir = find_lab_by_id(lab_id)
    if not lab_dir:
        return None, f"Lab '{lab_id}' not found."

    context, message = prepare(lab_id)
    if not context:
        return None, message

    # -------------------------------------------------
    # 🚦 Preflight (Docker ONLY — hard rule)
    # -------------------------------------------------
    ok, error = check_dependencies(
        required=[],      # users install Docker only
        runtime="docker",
    )
    if not ok:
        return None, error

    # -------------------------------------------------
    # 🐳 Resolve Docker services (ALWAYS)
    # -------------------------------------------------
    execution = context.get("execution", {}) or {}
    stack = context.get("stack")

    services = execution.get("services")

    if not services:
        default = DEFAULT_DOCKER_SERVICE.get(stack, FALLBACK_SERVICE)
        services = [default]

    # Normalize services
    if isinstance(services, str):
        services = [services]

    context["execution"]["runtime"] = "docker"
    context["execution"]["services"] = services

    return context, message


# -------------------------------------------------
# Validate (UNCHANGED)
# -------------------------------------------------
def validate_only(
    lab_id: Optional[str] = None,
    xp: Optional[int] = None,
):
    _ensure_profile_loaded()

    if not lab_id:
        return {"error": "Please provide a lab id."}

    lab_dir = find_lab_by_id(lab_id)
    if not lab_dir:
        return {"error": f"Lab '{lab_id}' not found."}

    meta_file = lab_dir / "lab.yaml"
    try:
        meta = yaml.safe_load(meta_file.read_text()) or {}
    except Exception:
        meta = {}

    before_state = load_state()
    before_badges = set(before_state.get("badges", []))
    before_xp = before_state.get("xp", {}).get("labs", 0)

    result = _validate_only(
        lab_id=lab_id,
        stack=meta.get("stack"),
        difficulty=meta.get("difficulty"),
        skills=meta.get("skills", []),
        xp=xp,
    )

    state = load_state()
    attempts = state.setdefault("attempts", {})

    if isinstance(result, dict) and result.get("error"):
        attempts[lab_id] = attempts.get(lab_id, 0) + 1
        save_state(state)
        return result

    attempts.pop(lab_id, None)
    save_state(state)

    after_state = load_state()
    after_badges = set(after_state.get("badges", []))
    after_xp = after_state.get("xp", {}).get("labs", 0)

    # -------------------------------------------------
    # 🔒 HARD GUARANTEE: engine ALWAYS returns badges
    # -------------------------------------------------
    earned_badges = sorted(after_badges - before_badges)

    if not isinstance(result, dict):
        result = {}

    result["earned_badges"] = earned_badges

    xp_delta = after_xp - before_xp
    if xp_delta > 0:
        result["xp_message"] = f"+{xp_delta} lab"

    return result


# -------------------------------------------------
# Stats
# -------------------------------------------------
def stats():
    data = _stats()
    return (
        f"👤 {data.get('username')}\n"
        f"🧠 XP: {data.get('xp')}\n"
        f"🏅 Rank: {data.get('profile', {}).get('rank')}\n"
        f"✅ Completed: {len(data.get('progress', {}).get('completed', []))}"
    )


__all__ = ["start", "validate_only", "stats"]
