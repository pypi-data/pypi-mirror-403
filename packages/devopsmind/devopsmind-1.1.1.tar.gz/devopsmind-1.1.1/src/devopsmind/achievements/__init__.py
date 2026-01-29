from pathlib import Path
import yaml
from importlib import resources
from math import ceil
from datetime import datetime
from dataclasses import dataclass

from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.console import Console

console = Console()

ACHIEVEMENTS_PACKAGE = "devopsmind.achievements"
PAGE_SIZE = 20


def _bell():
    print("\a", end="", flush=True)


# -------------------------------------------------
# 🔐 IDEMPOTENT BADGE AWARD GATE
# -------------------------------------------------
def _award_badge_once(state, badge_id):
    badges = state.setdefault("badges", [])
    if badge_id in badges:
        return False
    badges.append(badge_id)
    return True


# -------------------------------------------------
# Load achievement YAMLs (excluding milestones)
# -------------------------------------------------
def _load_achievements():
    achievements = []
    try:
        root = resources.files(ACHIEVEMENTS_PACKAGE)
        for file in sorted(root.iterdir()):
            if file.suffix == ".yaml" and file.name != "milestones.yaml":
                data = yaml.safe_load(file.read_text()) or []
                if isinstance(data, list):
                    achievements.extend(data)
    except Exception:
        return []
    return achievements


# -------------------------------------------------
# 🎖️ RARITY RESOLUTION (OFFLINE, DETERMINISTIC)
# -------------------------------------------------
def _rarity_from_condition(condition):
    """
    Heuristic rarity estimation based on condition strictness.
    Cosmetic only. Offline-safe.
    """
    if "special" in condition:
        return "Legendary"

    if "difficulty_completed_gte" in condition:
        diff = next(iter(condition["difficulty_completed_gte"]))
        return {
            "expert": "Epic",
            "master": "Mythic",
        }.get(diff, "Rare")

    if "stack_completed_gte" in condition:
        return "Rare"

    if "completed_gte" in condition:
        n = condition["completed_gte"]
        if n >= 50:
            return "Epic"
        if n >= 10:
            return "Rare"
        return "Common"

    return "Common"


RARITY_ICON = {
    "Common": "•",
    "Rare": "◆",
    "Epic": "★",
    "Legendary": "✦",
    "Mythic": "⬢",
}

RARITY_STYLE = {
    "Common": "dim",
    "Rare": "cyan",
    "Epic": "magenta",
    "Legendary": "yellow bold",
    "Mythic": "red bold",
}


def _format_rarity(rarity: str) -> Text:
    icon = RARITY_ICON.get(rarity, "•")
    style = RARITY_STYLE.get(rarity, "")
    return Text(f"{rarity} {icon}", style=style)


# -------------------------------------------------
# 🔐 SPECIAL CONDITION COMPUTATION
# -------------------------------------------------
def _compute_special_flags(state):
    now = datetime.now()
    progress = state.get("progress", {})
    failures = state.get("validation_failures", {})
    completed = progress.get("completed", [])

    last_played = state.get("last_played_at")
    days_since_last = (
        (now - datetime.fromisoformat(last_played)).days
        if last_played else None
    )

    by_stack = progress.get("by_stack", {})
    by_difficulty = progress.get("by_difficulty", {})

    last_failures = failures.get(completed[-1], 0) if completed else 0

    return {
        "night_play": now.hour < 5,
        "early_play": now.hour < 6,
        "first_midnight": now.hour < 5 and len(completed) == 1,
        "flawless_run": last_failures == 0,
        "flawless_first": last_failures == 0 and len(completed) == 1,
        "first_try_success": last_failures == 0,
        "first_expert_clear": by_difficulty.get("expert", 0) == 1,
        "first_master_clear": by_difficulty.get("master", 0) == 1,
        "week_streak": state.get("streak_days", 0) >= 7,
        "long_gap_return": days_since_last is not None and days_since_last >= 14,
        "multi_stack_explorer": len(by_stack) >= 5,
        "halloween_event": now.month == 10 and 25 <= now.day <= 31,
        "winter_event": now.month in (12, 1, 2),
        "new_year_event": now.month == 1 and now.day <= 7,
    }


# -------------------------------------------------
# Condition evaluator (NO XP CONDITIONS)
# -------------------------------------------------
def _evaluate(condition, state):
    progress = state.get("progress", {})
    special = state.get("special", {})

    if "completed_gte" in condition:
        return len(progress.get("completed", [])) >= condition["completed_gte"]

    if "difficulty_completed_gte" in condition:
        k, v = next(iter(condition["difficulty_completed_gte"].items()))
        return progress.get("by_difficulty", {}).get(k, 0) >= v

    if "stack_completed_gte" in condition:
        k, v = next(iter(condition["stack_completed_gte"].items()))
        return progress.get("by_stack", {}).get(k, 0) >= v

    if "special" in condition:
        return special.get(condition["special"], False)

    return False


# -------------------------------------------------
# 🎉 DELTA BANNER (BADGES ONLY)
# -------------------------------------------------
def show_badges():
    from devopsmind.progress import load_state, save_state, persist_earned_badges

    state = load_state()
    achievements = _load_achievements()

    state["special"] = _compute_special_flags(state)
    newly_unlocked = []

    for ach in achievements:
        if _evaluate(ach["condition"], state):
            if _award_badge_once(state, ach["id"]):
                newly_unlocked.append(ach)

    if newly_unlocked:
        persist_earned_badges(state, [a["id"] for a in newly_unlocked])
        save_state(state)
        _bell()

        return Panel.fit(
            "\n".join(f"{a.get('icon','🏅')} {a['name']}" for a in newly_unlocked),
            title="🎉 Achievement Unlocked!",
            border_style="yellow",
        )

    save_state(state)
    return None


# -------------------------------------------------
# 📋 LIST VIEW
# -------------------------------------------------
def list_badges(raw: bool = False):
    from devopsmind.progress import load_state

    state = load_state()
    achievements = _load_achievements()
    unlocked = [a for a in achievements if a["id"] in state.get("badges", [])]

    if raw:
        return achievements

    if not unlocked:
        return "No badges earned yet."

    total_pages = max(1, ceil(len(unlocked) / PAGE_SIZE))
    page = 1

    while True:
        page_badges = unlocked[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

        table = Table(title="🏅 Achievements", show_header=True)
        table.add_column("Icon")
        table.add_column("Name")
        table.add_column("Rarity")

        for ach in page_badges:
            rarity = _rarity_from_condition(ach.get("condition", {}))
            table.add_row(
                ach.get("icon", "🏅"),
                ach["name"],
                _format_rarity(rarity),
            )

        console.clear()
        console.print(table)
        console.print(f"\nPage {page}/{total_pages}  n/p/q")

        choice = input("> ").strip().lower()
        if choice == "n" and page < total_pages:
            page += 1
        elif choice == "p" and page > 1:
            page -= 1
        elif choice == "q":
            break

    return None


# -------------------------------------------------
# 🎯 Milestones (DATA ONLY — NO XP)
# -------------------------------------------------
@dataclass(frozen=True)
class Milestone:
    id: str
    completed_gte: int


def load_milestones():
    milestones_file = resources.files(ACHIEVEMENTS_PACKAGE) / "milestones.yaml"
    if not milestones_file.exists():
        return []

    data = yaml.safe_load(milestones_file.read_text()) or []
    milestones = []

    for m in data:
        cond = m.get("condition", {})
        if "completed_gte" in cond:
            milestones.append(
                Milestone(
                    id=m["id"],
                    completed_gte=cond["completed_gte"],
                )
            )

    return milestones
