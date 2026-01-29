from pathlib import Path
import re


def validate():
    """
    Validate authority boundaries for AI participation in incident triage.

    Enforces:
    - Explicit separation between assistance and triage authority
    - Clear human ownership of urgency, ownership, and escalation decisions
    - No implicit delegation of triage control to AI
    """

    submission_file = Path("triage-boundary.md")

    if not submission_file.exists():
        return False, "triage-boundary.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Triage boundary document is empty."

    # ---- structural requirements ----
    required_sections = [
        "# ai participation boundary",
        "# human control points",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section.title()}"

    # ---- reject untouched template scaffolding ----
    template_markers = [
        "define clearly",
        "use clear statements",
        "replace this section",
        "write in your own words",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Template scaffolding must be replaced."

    # ---- assistance boundary must exist ----
    if "ai" not in lowered or "may" not in lowered:
        return False, "AI participation boundary is not clearly articulated."

    # ---- authority boundary must exist ----
    if "must not" not in lowered and "cannot" not in lowered:
        return False, "Human triage control boundary is not clearly articulated."

    # ---- detect AI-as-triage-author framing ----
    ai_triage_patterns = [
        r"ai\s+(assigns|assigned)\s+(severity|owner|ownership)",
        r"ai\s+(decides|determines)\s+(severity|priority|escalation)",
        r"ai\s+(routes|escalates)\s+(incident|alerts)",
        r"incident\s+(is|was|will be)\s+(classified|triaged)\s+by\s+ai",
    ]

    for pattern in ai_triage_patterns:
        if re.search(pattern, lowered):
            return False, "AI is framed as having triage control authority."

    # ---- detect implicit delegation ----
    if "default" in lowered and "ai" in lowered:
        return False, "AI decisions are treated as defaults."

    if "unless overridden" in lowered:
        return False, "Human control is framed as an exception."

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

    return True, "Incident triage authority boundaries validated."
