# src/devopsmind/mentor/engine.py

from devopsmind.mentor.providers.rule_based import RuleBasedMentor
from devopsmind.mentor.providers.paid_stub import PaidMentor
from devopsmind.mentor.providers.ember_stub import EmberMentor
from devopsmind.mentor.stagnation import detect_stagnation_once
from devopsmind.state import load_state

from devopsmind.mentor.utils import (
    derive_lab_reason,
    derive_stack_balance,
    derive_focus_horizon,
    style_action_for,
)

from devopsmind.tiers.loader import load_owned_tiers
from devopsmind.list.lab_resolver import find_lab_by_id
from devopsmind.handlers.lab_utils import load_lab_metadata
from devopsmind.handlers.id_normalizer import canonical_id


# -------------------------------------------------
# Mentor Health Check (SAFE FOR DOCTOR)
# -------------------------------------------------

def mentor_healthcheck() -> bool:
    state = load_state() or {}

    if state.get("ember_enabled"):
        EmberMentor()
    elif state.get("paid_entitlement"):
        PaidMentor()
    else:
        RuleBasedMentor()

    return True


# -------------------------------------------------
# Mentor Advice Engine (MULTI-TIER)
# -------------------------------------------------

def get_mentor_advice():
    """
    Multi-tier mentor engine.

    Guarantees:
    - Recommendations per tier
    - Confidence per tier
    - No tier mixing
    - Mirrors `devopsmind stacks`
    """

    state = load_state() or {}
    progress = state.get("progress", {})
    completed_global = {canonical_id(c) for c in progress.get("completed", [])}

    if state.get("ember_enabled"):
        provider = EmberMentor()
    elif state.get("paid_entitlement"):
        provider = PaidMentor()
    else:
        provider = RuleBasedMentor()

    raw = provider.generate() or {}

    owned_tiers = load_owned_tiers() or []

    # -------------------------------------------------
    # ✅ PRIMARY: provider-driven recommendations per tier
    # -------------------------------------------------

    recommendations_by_tier = raw.get("recommendations_by_tier", {})
    confidence_by_tier = raw.get("confidence_by_tier", {})

    # -------------------------------------------------
    # FALLBACK: started tiers MUST get guidance
    # (derive started state from GLOBAL progress)
    # -------------------------------------------------

    for tier in owned_tiers:
        tier_name = tier.get("name") or tier.get("tier")

        if tier_name in recommendations_by_tier:
            continue

        tier_lab_ids = {canonical_id(i) for i in tier.get("lab_ids", [])}
        completed_in_tier = tier_lab_ids & completed_global

        if not completed_in_tier:
            continue  # tier truly not started

        fallback = []

        for lab_id in tier_lab_ids:
            if lab_id in completed_global:
                continue

            lab_dir = find_lab_by_id(lab_id)
            if not lab_dir:
                continue

            try:
                meta = load_lab_metadata(lab_dir)
            except Exception:
                continue

            if meta.get("difficulty") != "Easy":
                continue

            meta["id"] = lab_id
            meta["reason"] = derive_lab_reason(
                meta.get("stack"),
                meta.get("difficulty"),
            )

            fallback.append(meta)

            if len(fallback) >= 2:
                break

        if fallback:
            recommendations_by_tier[tier_name] = fallback

    # -------------------------------------------------
    # Derived insights PER TIER
    # -------------------------------------------------

    stack_balance_by_tier = {}
    focus_horizon_by_tier = {}

    for tier_name, confidence in confidence_by_tier.items():
        stack_balance_by_tier[tier_name] = derive_stack_balance(confidence)
        focus_horizon_by_tier[tier_name] = derive_focus_horizon(confidence)

    # -------------------------------------------------
    # Learning style (GLOBAL SIGNAL)
    # -------------------------------------------------

    learning_style = raw.get("learning_style", {})
    style_action = None

    if isinstance(learning_style, dict):
        label = learning_style.get("label")
        if label:
            style_action = style_action_for(label)

    # -------------------------------------------------
    # Advancement lab PER TIER (optional)
    # -------------------------------------------------

    advancement_by_tier = {}

    for tier_name, recos in recommendations_by_tier.items():
        for c in recos:
            if c.get("difficulty") in ("Medium", "Hard"):
                advancement_by_tier[tier_name] = c
                break

    # -------------------------------------------------
    # Final mentor output
    # -------------------------------------------------

    return {
        "recommendations_by_tier": recommendations_by_tier,
        "confidence_by_tier": confidence_by_tier,
        "stack_balance_by_tier": stack_balance_by_tier,
        "focus_horizon_by_tier": focus_horizon_by_tier,
        "advancement_by_tier": advancement_by_tier,
        "learning_style": learning_style,
        "style_action": style_action,
        "cadence": raw.get("cadence", "3–4 focused sessions per week"),
        "stagnation": detect_stagnation_once(),
    }
