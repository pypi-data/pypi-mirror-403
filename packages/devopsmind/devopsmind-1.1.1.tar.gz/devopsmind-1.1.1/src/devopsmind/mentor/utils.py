# devopsmind/mentor/utils.py

from typing import Dict, List, Set


# -------------------------------------------------
# 🔹 Confidence labeling (ABSOLUTE, MATURITY-ALIGNED)
# -------------------------------------------------

def confidence_label(count: int) -> str:
    """
    Convert completed lab count into a qualitative confidence label.

    Aligned with mentor maturity logic:
    - Prevents premature 'Confident' signals
    - Cold-start safe
    """

    if count <= 0:
        return "🌱 Unexplored"
    if count == 1:
        return "🧩 Emerging"
    if count == 2:
        return "🧠 Familiar"
    if count <= 4:
        return "🏗️ Working"
    return "🧘 Confident"


# -------------------------------------------------
# 🔹 Derived explanations (NO hardcoding)
# -------------------------------------------------

def derive_lab_reason(stack: str, difficulty: str) -> str:
    """
    Explain why a lab is recommended using metadata only.
    No lab IDs, no static mappings.
    """

    stack = (stack or "").lower()
    difficulty = (difficulty or "").lower()

    if difficulty == "easy":
        intent = "builds fundamentals"
    elif difficulty == "medium":
        intent = "strengthens practical problem-solving"
    elif difficulty == "hard":
        intent = "develops real-world troubleshooting depth"
    else:
        intent = "pushes advanced mastery"

    if stack in ("bash", "linux"):
        domain = "system understanding and command-line fluency"
    elif stack in ("docker", "kubernetes", "helm"):
        domain = "containerized application thinking"
    elif stack in ("terraform", "ansible"):
        domain = "infrastructure automation patterns"
    elif stack == "git":
        domain = "version control confidence"
    elif stack == "python":
        domain = "automation and scripting skills"
    elif stack == "networking":
        domain = "network behavior awareness"
    else:
        domain = "core DevOps skills"

    return f"This {intent} by reinforcing {domain}."


# -------------------------------------------------
# 🔹 Stack balance insight (COLD-START SAFE)
# -------------------------------------------------

def derive_stack_balance(confidence: Dict[str, Dict[str, int]]) -> str | None:
    """
    Derive stack balance insight.

    Cold-start safe:
    - Prevents 'strongest' claims when progress is minimal
    - Uses absolute completion threshold before strong language
    """

    if not confidence:
        return None

    completed_map = {
        stack: data.get("completed", 0)
        for stack, data in confidence.items()
    }

    ordered = sorted(
        completed_map.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    top_stack, top_completed = ordered[0]

    # -------------------------------------------------
    # 🧊 Cold-start guard
    # -------------------------------------------------
    if top_completed < 3:
        started = [
            stack.title()
            for stack, count in ordered
            if count > 0
        ]

        if started:
            return (
                f"You’ve started building momentum in {started[0]}. "
                "Most other stacks are still unexplored, so this is an early signal."
            )

        return (
            "Most stacks are still unexplored. Early progress will help the mentor "
            "identify your strengths more clearly."
        )

    # -------------------------------------------------
    # Mature signal
    # -------------------------------------------------
    weak = [
        stack.title()
        for stack, count in ordered
        if count == 0
    ]

    if weak:
        return (
            f"You’re strongest in {top_stack.title()}. "
            f"{', '.join(weak[:3])} will give the fastest overall gains right now."
        )

    return (
        f"You’re showing balanced progress, with {top_stack.title()} "
        "currently leading in completed labs."
    )


# -------------------------------------------------
# 🔹 Focus horizon (time-boxed guidance)
# -------------------------------------------------

def derive_focus_horizon(confidence: Dict[str, Dict[str, int]]) -> str | None:
    weak = []

    for stack, data in confidence.items():
        completed = data.get("completed", 0)
        total = max(data.get("total", 1), 1)
        if completed / total < 0.4:
            weak.append(stack.title())

    if weak:
        return f"Next 2–3 weeks → {', '.join(weak[:2])} fundamentals"

    return None


# -------------------------------------------------
# 🔹 Learning style → action hint
# -------------------------------------------------

def style_action_for(label: str) -> str | None:
    """
    Convert learning style into a single actionable mentor hint.
    """
    if label == "Specialist":
        return "Stay with one stack for a full week before switching."
    if label == "Explorer":
        return "Rotate stacks every few sessions to keep momentum."
    if label == "Balancer":
        return "Alternate between a comfort stack and a stretch stack."
    return None


# -------------------------------------------------
# 🔹 Stretch lab (NEXT UNSEEN IN SAME STACK)
# -------------------------------------------------

def derive_stretch_lab(
    stack: str,
    all_labs: List[Dict],
    completed_ids: Set[str],
) -> Dict | None:
    """
    Stretch lab logic:

    - Same stack as primary recommendation
    - Next unseen lab
    - Order-preserving
    - No difficulty hardcoding
    - Advisory only (NOT unlock logic)

    This is intentional progressive depth, not breadth.
    """

    if not stack:
        return None

    for lab in all_labs:
        if lab.get("stack") != stack:
            continue
        if lab.get("id") in completed_ids:
            continue
        return lab

    return None

