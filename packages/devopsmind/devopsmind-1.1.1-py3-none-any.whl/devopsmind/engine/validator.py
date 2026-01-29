from pathlib import Path
import importlib.util
import os
import subprocess

from rich.text import Text

from devopsmind.progress import record_completion, load_state, save_state
from devopsmind.restore.sync import attempt_sync
from devopsmind.badges import evaluate_badges_delta
from devopsmind.list.lab_resolver import find_lab_by_id
from devopsmind.streak import update_streak_on_success
from .hint import load_hints_for_lab

# 🔒 Safety executor
from devopsmind.safety.executor import safe_run

# ✅ Shared metadata loader
from devopsmind.handlers.lab_utils import load_lab_metadata

# 🆕 VALIDATION ENV HANDLER (ONLY ADDITION)
from devopsmind.handlers.validate_env import run_validate_env


WORKSPACE_DIR = Path.home() / "workspace"
PLAY_MARKER = ".devopsmind_played"
FAIL_LIMIT = 3

ACHIEVEMENTS_DIR = Path(__file__).parent / "achievements"


# -------------------------------------------------
# Achievement Registry
# -------------------------------------------------
def _load_achievement_registry():
    registry = {}

    if not ACHIEVEMENTS_DIR.exists():
        return registry

    for file in ACHIEVEMENTS_DIR.glob("*.yaml"):
        raw = file.read_text()
        import yaml
        entries = yaml.safe_load(raw) or []

        for ach in entries:
            registry[ach["id"]] = {
                "name": ach.get("name", ach["id"]),
                "icon": ach.get("icon", ""),
            }

    return registry


_ACHIEVEMENT_REGISTRY = _load_achievement_registry()


def _resolve_achievement_display(ids):
    resolved = []
    for ach_id in ids:
        meta = _ACHIEVEMENT_REGISTRY.get(ach_id)
        if meta:
            resolved.append(f"{meta['icon']} {meta['name']}".strip())
        else:
            resolved.append(ach_id)
    return resolved


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _workspace(lab_id):
    return WORKSPACE_DIR / lab_id


def _cwd_matches_workspace(lab_id):
    try:
        return Path.cwd().resolve() == _workspace(lab_id).resolve()
    except Exception:
        return False


def _was_played(lab_id):
    return (_workspace(lab_id) / PLAY_MARKER).exists()


def _has_active_workspace(lab_id):
    ws = _workspace(lab_id)
    return (
        ws.exists()
        and (ws / PLAY_MARKER).exists()
        and not (ws / ".devopsmind_success").exists()
    )


def _increment_fail(lab_id):
    state = load_state()
    failures = state.setdefault("validation_failures", {})
    failures[lab_id] = failures.get(lab_id, 0) + 1
    save_state(state)
    return failures[lab_id]


def _reset_fail(lab_id):
    state = load_state()
    failures = state.get("validation_failures", {})
    if lab_id in failures:
        del failures[lab_id]
        save_state(state)


def _cleanup_lab_secret(lab_id):
    state = load_state()
    secrets = state.get("lab_secrets", {})
    if lab_id in secrets:
        del secrets[lab_id]
        save_state(state)


# -------------------------------------------------
# Lab Validator Runner
# -------------------------------------------------
def _run_lab_validator(lab_id):
    ws = _workspace(lab_id)
    lab_dir = find_lab_by_id(lab_id)

    if not lab_dir:
        return False, "Lab source not found."

    validator_file = lab_dir / "validator.py"
    if not validator_file.exists():
        return False, "Lab validator not found."

    # 🔒 Patch subprocess.run + os.system
    if not hasattr(subprocess, "_original_run"):
        subprocess._original_run = subprocess.run
    if not hasattr(os, "_original_system"):
        os._original_system = os.system

    subprocess.run = safe_run
    os.system = lambda cmd: safe_run(cmd.split())

    old_env = os.environ.copy()

    try:
        # -------------------------------------------------
        # 🧪 Validation env delegation (ONLY CHANGE)
        # -------------------------------------------------
        injected_env = run_validate_env(
            lab_id=lab_id,
            lab_dir=lab_dir,
        )

        os.environ.update(injected_env)

        spec = importlib.util.spec_from_file_location(
            f"validator_{lab_id}", validator_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "validate"):
            return False, "Validator must define validate()"

        cwd = os.getcwd()
        try:
            os.chdir(ws)
            result = module.validate()
        finally:
            os.chdir(cwd)

        if not isinstance(result, tuple) or len(result) != 2:
            return False, "Validator must return (bool, message)"

        return bool(result[0]), str(result[1])

    except Exception as e:
        return False, f"Validator error: {e}"

    finally:
        os.environ.clear()
        os.environ.update(old_env)
        subprocess.run = subprocess._original_run
        os.system = os._original_system

# -------------------------------------------------
# Validator (CORE)
# -------------------------------------------------
def validate_only(
    lab_id,
    stack=None,
    difficulty=None,
    skills=None,
    xp=None,
):
    ws = _workspace(lab_id)

    if not ws.exists():
        return {
            "error": (
                "Lab is not active.\n"
                f"Run: `devopsmind start {lab_id}` to begin the lab."
            )
        }

    if not _was_played(lab_id):
        return {
            "error": (
                "Lab not started.\n"
                f"Run: `devopsmind start {lab_id}`"
            )
        }

    if not _cwd_matches_workspace(lab_id):
        if os.environ.get("DEVOPSMIND_SAFE") != "1":
            if _has_active_workspace(lab_id):
                return {
                    "error": (
                        "This lab is already in progress.\n"
                        f"Run: `devopsmind resume {lab_id}` to resume."
                    )
                }

            return {
                "error": (
                    "Lab is not active.\n"
                    f"Run: `devopsmind start {lab_id}` to begin."
                )
            }

        return {
            "error": f"Validation must be run from the lab workspace.\ncd {ws}"
        }

    success, message = _run_lab_validator(lab_id)

    if not success:
        attempts = _increment_fail(lab_id)
        auto_hint = None
        hints = load_hints_for_lab(lab_id)

        if hints:
            hint_block = Text("💡 Insights\n", style="bold")

            if attempts < 3:
                remaining = 3 - attempts
                hint_block.append(
                    f"\n🔒 Insight unlocks in {remaining} attempt"
                    f"{'s' if remaining > 1 else ''}.",
                    style="dim",
                )
            else:
                # 3–4 → hint 0
                # 5–6 → hint 1
                index = min((attempts - 3) // 2, len(hints) - 1)

                hint_block.append("\n\nInsight:\n", style="bold yellow")
                hint_block.append(hints[index], style="yellow")

            auto_hint = hint_block

        return {
            "error": message,
            "attempts": attempts,
            "fail_limit": FAIL_LIMIT,
            "auto_hint": auto_hint,
        }

    _reset_fail(lab_id)
    _cleanup_lab_secret(lab_id)
    update_streak_on_success()

    try:
        (ws / ".devopsmind_success").write_text("validated")
    except Exception:
        pass

    mentor_after = None
    lab_dir = find_lab_by_id(lab_id)
    if lab_dir:
        meta = load_lab_metadata(lab_dir)
        mentor_after = meta.get("mentor", {}).get("guidance", {}).get("after")

    badge_result = evaluate_badges_delta(
        record_completion,
        lab_id=lab_id,
        stack=stack,
        difficulty=difficulty,
        lab_xp=xp,
    )

    new_badges = badge_result.get("badges", [])
    milestone_bonus = badge_result.get("milestone_bonus", 0)

    achievements = _resolve_achievement_display(new_badges) if new_badges else []

    raw_sync = attempt_sync()
    sync_status = (
        {"info": "No changes to sync."}
        if isinstance(raw_sync, dict) and raw_sync.get("already")
        else raw_sync
    )

    return {
        "lab_id": lab_id,
        "lab_label": f"Lab: {load_lab_metadata(find_lab_by_id(lab_id)).get('title', lab_id)}",
        "stack": stack,
        "difficulty": difficulty,
        "skills": skills or [],
        "xp_awarded": xp,
        "milestone_bonus": milestone_bonus,
        "message": message,
        "achievements": achievements,
        "mentor_after": mentor_after,
        "sync_status": sync_status,
    }
