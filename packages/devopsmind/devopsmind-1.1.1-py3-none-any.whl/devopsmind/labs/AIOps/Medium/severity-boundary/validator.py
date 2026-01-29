from pathlib import Path
import re


def validate():
    """
    Validate authority boundaries for AI-assisted incident severity changes.

    Enforces:
    - Explicit separation between assessment and severity authority
    - Clear human ownership of urgency and visibility changes
    - No delegation of severity modification to AI
    """

    submission_file = Path("severity-boundary.md")

    if not submission_file.exists():
        return False, "severity-boundary.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Severity boundary document is empty."

    # ---- structural requirements ----
    required_sections = [
        "# ai severity boundary",
        "# mandatory human severity decisions",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section.title()}"

    # ---- reject untouched template scaffolding ----
    template_markers = [
        "define clearly",
        "use explicit statements",
        "replace this section",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Template scaffolding must be replaced."

    # ---- assistance boundary must exist ----
    if "ai" not in lowered or "may" not in lowered:
        return False, "AI assistance boundary is not clearly articulated."

    # ---- authority boundary must exist ----
    if "must not" not in lowered and "cannot" not in lowered:
        return False, "Human severity authority boundary is not clearly articulated."

    # ---- detect AI-as-severity-controller framing ----
    ai_severity_patterns = [
        r"ai\s+(changes|changed|changing)\s+severity",
        r"ai\s+(downgrades|upgrades|reclassifies)",
        r"severity\s+(is|was|will be)\s+(changed|adjusted)\s+by\s+ai",
        r"ai\s+(decides|determines)\s+severity",
    ]

    for pattern in ai_severity_patterns:
        if re.search(pattern, lowered):
            return False, "AI is framed as having severity control authority."

    # ---- detect silent downgrade risk ----
    downgrade_patterns = [
        r"automatically\s+(downgrade|lower)\s+severity",
        r"reduce\s+severity\s+without",
    ]

    for pattern in downgrade_patterns:
        if re.search(pattern, lowered):
            return False, "Severity downgrade authority is implicitly delegated."

    # ---- detect deferred ownership ----
    if "can be corrected later" in lowered or "later correction" in lowered:
        return False, "Severity authority is deferred rather than owned."

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

    return True, "Incident severity authority boundaries validated."
