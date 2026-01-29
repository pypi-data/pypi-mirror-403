# src/devopsmind/mentor/providers/rule_based.py

import yaml
from pathlib import Path

from devopsmind.state import load_state
from devopsmind.list.lab_resolver import list_all_labs, find_lab_by_id
from devopsmind.handlers.lab_utils import load_lab_metadata
from devopsmind.mentor.rotation import load_rotation_memory, save_rotation_memory
from devopsmind.mentor.stagnation import detect_stagnation_once
from devopsmind.mentor.utils import (
    derive_lab_reason,
    derive_stack_balance,
    derive_focus_horizon,
    style_action_for,
)
from devopsmind.handlers.id_normalizer import canonical_id

# ✅ ENTITLEMENT SOURCE OF TRUTH
from devopsmind.tiers.tier_loader import load_visible_lab_ids


TIERS_DIR = Path.home() / ".devopsmind" / "tiers"


# -------------------------------------------------
# Difficulty helpers
# -------------------------------------------------

DIFFICULTY_WEIGHT = {
    "Easy": 0.3,
    "Medium": 0.6,
    "Hard": 0.9,
    "Expert": 1.2,
}

DIFFICULTY_ORDER = ["easy", "medium", "hard", "expert"]


def difficulty_index(lab):
    diff = (lab.get("difficulty") or "medium").lower()
    return DIFFICULTY_ORDER.index(diff) if diff in DIFFICULTY_ORDER else 1


# -------------------------------------------------
# Tier helpers
# -------------------------------------------------

def _load_tier_ids(filename: str) -> set[str]:
    path = TIERS_DIR / filename
    if not path.exists():
        return set()

    try:
        data = yaml.safe_load(path.read_text()) or {}
    except Exception:
        return set()

    return {canonical_id(cid) for cid in data.get("lab_ids", [])}


def _effective_core_tiers():
    foundation = _load_tier_ids("foundation_core.yaml")
    core_pro = _load_tier_ids("core_pro.yaml")

    if core_pro:
        return {"Foundation Core": foundation, "Core Pro": core_pro | foundation}

    if foundation:
        return {"Foundation Core": foundation}

    return {}


# -------------------------------------------------
# Rule-Based Mentor
# -------------------------------------------------

class RuleBasedMentor:
    """
    Multi-tier mentor engine.

    Guarantees:
    - Recommendations per tier
    - Confidence per tier
    - Foundation + Domain tiers can coexist
    - Mirrors `devopsmind stacks`
    """

    def generate(self):
        state = load_state() or {}

        progress = state.get("progress", {})
        completed = {canonical_id(c) for c in progress.get("completed", [])}
        attempts = state.get("attempts", {})

        stuck_labs = {lab_id for lab_id, count in attempts.items() if count >= 3}
        rotation_memory = set(load_rotation_memory())

        # -------------------------------------------------
        # 🔒 ENTITLEMENT FILTER (VERSION-SAFE)
        # -------------------------------------------------
        visible_ids = {canonical_id(cid) for cid in load_visible_lab_ids()}

        # -------------------------------------------------
        # Load ALL labs (filtered later)
        # -------------------------------------------------

        all_labs = []
        for lab_id in list_all_labs():
            lab_dir = find_lab_by_id(lab_id)
            if not lab_dir:
                continue
            try:
                meta = load_lab_metadata(lab_dir)
            except Exception:
                continue
            meta["id"] = canonical_id(lab_id)
            all_labs.append(meta)

        # -------------------------------------------------
        # Learning style (GLOBAL)
        # -------------------------------------------------

        stacks_touched = len({c.get("stack") for c in all_labs if c["id"] in completed})
        total_completed = len(completed)

        if stacks_touched >= 4 and total_completed <= 10:
            learning_style = {
                "label": "Explorer",
                "explanation": "You spread effort across multiple stacks, building wide intuition early.",
            }
        else:
            learning_style = {
                "label": "Specialist",
                "explanation": "You prefer depth over breadth, staying with a topic until it feels solid.",
            }

        # -------------------------------------------------
        # Helper: build recos for a tier
        # -------------------------------------------------

        def build_recommendations(tier_lab_ids):
            candidates = [
                c for c in all_labs
                if c["id"] in tier_lab_ids
                and c["id"] in visible_ids
                and c["id"] not in completed
                and c["id"] not in stuck_labs
            ]

            # 🔰 FIRST-TIME USER BOOTSTRAP
            if not completed:
                recos = sorted(candidates, key=lambda c: difficulty_index(c))[:3]
                for c in recos:
                    c["reason"] = derive_lab_reason(c.get("stack"), c.get("difficulty"))
                return recos

            stack_scores = {}
            for lab in all_labs:
                if lab["id"] in tier_lab_ids and lab["id"] in visible_ids:
                    stack_scores.setdefault(lab.get("stack"), 0.0)

            for lab in all_labs:
                if lab["id"] in completed and lab["id"] in tier_lab_ids and lab["id"] in visible_ids:
                    stack = lab.get("stack")
                    stack_scores[stack] += DIFFICULTY_WEIGHT.get(
                        lab.get("difficulty", "Medium"), 0.6
                    )

            weak_stacks = sorted(stack_scores.items(), key=lambda x: x[1])
            recos = []

            for stack, _ in weak_stacks:
                if len(recos) >= 3:
                    break
                for c in candidates:
                    if (
                        c.get("stack") == stack
                        and (not rotation_memory or c["id"] not in rotation_memory)
                    ):
                        recos.append(c)
                        break

            if not recos:
                for c in candidates:
                    if len(recos) >= 3:
                        break
                    if not rotation_memory or c["id"] not in rotation_memory:
                        recos.append(c)

            for c in recos:
                c["reason"] = derive_lab_reason(c.get("stack"), c.get("difficulty"))

            return recos

        # -------------------------------------------------
        # Recommendations PER TIER
        # -------------------------------------------------

        recommendations_by_tier = {}

        # Core tiers
        for tier_name, tier_lab_ids in _effective_core_tiers().items():
            tier_lab_ids = {cid for cid in tier_lab_ids if cid in visible_ids}
            if tier_lab_ids:
                recos = build_recommendations(tier_lab_ids)
                if recos:
                    recommendations_by_tier[tier_name] = recos

        # Domain tiers
        for tier_file in TIERS_DIR.glob("domain_*.yaml"):
            try:
                tier_data = yaml.safe_load(tier_file.read_text()) or {}
            except Exception:
                continue

            tier_name = tier_data.get("name") or tier_file.stem.replace("domain_", "").title()
            tier_lab_ids = {
                canonical_id(cid)
                for cid in tier_data.get("lab_ids", [])
                if canonical_id(cid) in visible_ids
            }

            if tier_lab_ids:
                recos = build_recommendations(tier_lab_ids)
                if recos:
                    recommendations_by_tier[tier_name] = recos

        save_rotation_memory(
            [c["id"] for recos in recommendations_by_tier.values() for c in recos]
        )

        # -------------------------------------------------
        # Confidence PER TIER
        # -------------------------------------------------

        confidence_by_tier = {}

        def build_confidence(tier_lab_ids):
            scores = {}
            for lab in all_labs:
                if lab["id"] not in tier_lab_ids or lab["id"] not in visible_ids:
                    continue
                stack = lab.get("stack")
                if not stack:
                    continue
                scores.setdefault(stack, {"score": 0.0, "completed": 0})
                if lab["id"] in completed:
                    scores[stack]["completed"] += 1
                    scores[stack]["score"] += DIFFICULTY_WEIGHT.get(
                        lab.get("difficulty", "Medium"), 0.6
                    )

            final = {}
            for stack, data in scores.items():
                score = data["score"]
                if score <= 0:
                    label = "🌱 Unexplored"
                elif score < 1:
                    label = "🧩 Emerging"
                elif score < 9:
                    label = "🧠 Familiar"
                else:
                    label = "🧘 Confident"

                final[stack] = {"label": label, "completed": data["completed"]}
            return final

        for tier_name, tier_lab_ids in _effective_core_tiers().items():
            confidence_by_tier[tier_name] = build_confidence(
                {cid for cid in tier_lab_ids if cid in visible_ids}
            )

        for tier_file in TIERS_DIR.glob("domain_*.yaml"):
            tier_data = yaml.safe_load(tier_file.read_text()) or {}
            tier_name = tier_data.get("name") or tier_file.stem.replace("domain_", "").title()
            tier_lab_ids = {
                canonical_id(cid)
                for cid in tier_data.get("lab_ids", [])
                if canonical_id(cid) in visible_ids
            }

            if tier_lab_ids:
                confidence_by_tier[tier_name] = build_confidence(tier_lab_ids)

        # -------------------------------------------------
        # Final output
        # -------------------------------------------------

        return {
            "recommendations_by_tier": recommendations_by_tier,
            "confidence_by_tier": confidence_by_tier,
            "learning_style": learning_style,
            "cadence": "3–4 focused sessions per week",
            "stagnation": detect_stagnation_once(),
        }
