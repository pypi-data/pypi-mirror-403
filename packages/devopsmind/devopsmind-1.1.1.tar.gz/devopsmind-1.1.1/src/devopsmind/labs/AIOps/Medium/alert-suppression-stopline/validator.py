from pathlib import Path


def validate():
    """
    Validate explicit stop-lines for AI-based alert suppression.

    This validator enforces:
    - Explicit disengagement conditions
    - Enforceability without interpretation
    - Independence from AI confidence or self-assessment
    """

    submission_file = Path("suppression-stopline.md")

    if not submission_file.exists():
        return False, (
            "suppression-stopline.md is missing. Define stop-lines there."
        )

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, (
            "Stop-line document is empty. Explicit disengagement conditions are required."
        )

    # Required structure
    required_sections = [
        "# alert suppression stop-lines",
        "# mandatory re-exposure conditions",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, (
                f"Missing required section: {section.title()}"
            )

    # Reject template guidance
    template_phrases = [
        "define explicit conditions",
        "use clear, enforceable language",
        "avoid vague language",
        "write in your own words",
    ]

    for phrase in template_phrases:
        if phrase in lowered:
            return False, (
                "Template guidance must be replaced with concrete stop-line rules."
            )

    # Enforce explicit conditional framing
    conditional_markers = [
        "when ",
        "if ",
        "upon ",
        "once ",
        "whenever ",
    ]

    if not any(marker in lowered for marker in conditional_markers):
        return False, (
            "Stop-lines must be expressed as explicit conditions or events."
        )

    # Require automatic disengagement language
    disengagement_terms = [
        "must stop",
        "must disengage",
        "suppression ends",
        "alerts must be re-exposed",
        "full visibility restored",
    ]

    if not any(term in lowered for term in disengagement_terms):
        return False, (
            "Stop-lines must mandate automatic disengagement and alert re-exposure."
        )

    # Reject confidence or AI self-evaluation
    forbidden_terms = [
        "confidence",
        "model",
        "training",
        "prompt",
        "api",
        "accuracy",
        "ai decides",
        "ai determines",
    ]

    for term in forbidden_terms:
        if term in lowered:
            return False, (
                "Stop-lines must not depend on AI confidence or internal evaluation."
            )

    # Reject manual override dependency
    if "manual override" in lowered:
        return False, (
            "Manual override cannot be the primary stop-line safeguard."
        )

    return True, "Explicit alert suppression stop-lines defined."
