from .state import load_state

# -------------------------------------------------
# EXISTING FUNCTIONS (UNCHANGED)
# -------------------------------------------------

def show_badges():
    """
    Evaluate achievements and return a printable badge list.

    This is the PUBLIC entrypoint that:
    - loads achievement rules
    - evaluates them
    - persists newly earned badges
    """
    from devopsmind.achievements import show_badges as _evaluate_and_render

    # NOTE:
    # We intentionally call the achievements-layer function
    # to trigger evaluation side effects.
    return _evaluate_and_render()


# -------------------------------------------------
# Delta badge helper (FIXED: milestone-safe)
# -------------------------------------------------

def evaluate_badges_delta(trigger_fn, *args, **kwargs):
    """
    Generic wrapper to compute newly earned badges (delta).

    - DOES NOT contain badge rules
    - DOES NOT decide eligibility
    - Delegates evaluation to achievements layer
    - Milestones are FACT ONLY — NO XP
    """

    # Snapshot BEFORE
    state_before = load_state()
    before_badges = set(state_before.get("badges", []))
    before_milestones = set(state_before.get("milestones_awarded", []))

    # Run progress mutation (e.g. record_completion)
    trigger_fn(*args, **kwargs)

    # 🔒 Trigger achievement evaluation (PUBLIC API)
    show_badges()

    # Snapshot AFTER
    state_after = load_state()
    after_badges = set(state_after.get("badges", []))
    after_milestones = set(state_after.get("milestones_awarded", []))

    # 🔐 IDENTITY / IDEMPOTENCY LOCK
    # Badges must be monotonic — never removed or duplicated
    assert after_badges.issuperset(before_badges), (
        "Achievement state corruption detected: badges were removed or rewritten"
    )

    # Badge delta (unchanged behavior)
    new_badges = sorted(after_badges - before_badges)

    # Milestone delta (FACT ONLY — NO XP)
    newly_awarded_milestones = after_milestones - before_milestones

    # Cosmetic only (explicitly zero by contract)
    milestone_xp = 0

    return {
        "badges": new_badges,
        "milestone_bonus": milestone_xp,
    }
