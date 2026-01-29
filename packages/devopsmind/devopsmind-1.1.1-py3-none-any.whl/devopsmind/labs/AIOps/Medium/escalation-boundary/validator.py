from pathlib import Path
import re


def validate():
    """
    Validate authority boundaries for AI-assisted incident escalation.

    Enforces:
    - Explicit separation between assessment and escalation authority
    - Clear human ownership of responsibility transfer
    - No delegation of escalation or paging decisions to AI
    """

    submission_file = Path("escalation-boundary.md")

    if not submission_file.exists():
        return False, "escalation-boundary.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Escalation boundary document is empty."

    # ---- structural requirements ----
    required_sections = [
        "# ai escalation boundary",
        "# mandatory human authority points",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section.title()}"

    # ---- reject untouched template scaffolding ----
    template_markers = [
        "define clearly",
        "use explicit",
        "replace this section",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Template scaffolding must be replaced."

    # ---- assistance boundary must exist ----
    if "ai" not in lowered or "may" not in lowered:
        return False, "AI assistance boundary is not clearly articulated."

    # ---- authority boundary must exist ----
    if "must not" not in lowered and "cannot" not in lowered:
        return False, "Human escalation authority boundary is not clearly articulated."

    # ---- detect AI-as-escalator framing (loose, semantic) ----
    ai_escalation_patterns = [
        r"ai\s+(escalates|escalated|escalating)",
        r"ai\s+(pages|paged|paging)",
        r"ai\s+(alerts|notifies)\s+(on[-\s]?call|teams|management)",
        r"incident\s+(is|was|will be)\s+escalated\s+by\s+ai",
        r"ai\s+(decides|determines)\s+(when|whether)\s+to\s+escalate",
    ]

    for pattern in ai_escalation_patterns:
        if re.search(pattern, lowered):
            return False, "AI is framed as having escalation or paging authority."

    # ---- detect deferred ownership (escalation safety theater) ----
    if "manual review" in lowered or "review after escalation" in lowered:
        return False, "Escalation authority is deferred rather than owned."

    if "can be corrected" in lowered or "easily corrected" in lowered:
        return False, "Escalation risk is minimized rather than owned."

    # ---- forbid ML / tooling framing ----
    forbidden_terms = [
        "model",
        "training",
        "prompt",
        "api",
        "pipeline",
        "accuracy",
        "confidence",
    ]

    if any(term in lowered for term in forbidden_terms):
        return False, "Tooling or ML framing detected."

    return True, "Incident escalation authority boundaries validated."
