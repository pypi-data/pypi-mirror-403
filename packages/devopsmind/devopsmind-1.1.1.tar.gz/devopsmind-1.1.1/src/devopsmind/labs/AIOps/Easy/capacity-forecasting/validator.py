from pathlib import Path


def validate():
    """
    Validate operational judgment for AI-based capacity forecasting.

    This validator enforces reasoning about reversibility,
    uncertainty, and accountability — not prediction accuracy.
    """

    submission_file = Path("approval-note.md")

    if not submission_file.exists():
        return False, (
            "decision.md is missing. Record your capacity forecasting decision there."
        )

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Submission is empty. A written judgment is required."

    # Required structure
    for section in ["# decision", "# risk and reversibility"]:
        if section not in lowered:
            return False, (
                "Submission must include Decision and Risk and Reversibility sections."
            )

    # Reject template language
    template_phrases = [
        "record your decision",
        "use the questions below",
        "do not copy them into your response",
        "write in your own words",
        "do not describe implementation details",
    ]

    for phrase in template_phrases:
        if phrase in lowered:
            return False, (
                "Template guidance must be replaced with original operational reasoning."
            )

    # Explicit YES / NO
    decision_block = lowered.split("# decision", 1)[1]
    if not any(term in decision_block for term in ["yes", "no"]):
        return False, "Decision section must explicitly state YES or NO."

    # Reversibility awareness
    reversibility_terms = [
        "reversible",
        "irreversible",
        "hard to reverse",
        "long-term",
        "commitment",
    ]

    if not any(term in lowered for term in reversibility_terms):
        return False, (
            "Risk analysis must address reversibility or long-term commitment."
        )

    # Risk awareness
    risk_terms = [
        "risk",
        "uncertainty",
        "wrong forecast",
        "over-provision",
        "under-provision",
        "impact",
    ]

    if not any(term in lowered for term in risk_terms):
        return False, (
            "Risk assessment does not demonstrate awareness of forecast uncertainty."
        )

    # Accountability
    accountability_terms = [
        "human",
        "engineer",
        "team",
        "accountab",
        "responsib",
        "owned",
    ]

    if not any(term in lowered for term in accountability_terms):
        return False, (
            "Human accountability for capacity decisions must be explicit."
        )

    # Reject implementation framing
    forbidden_terms = [
        "model",
        "training",
        "prompt",
        "api",
        "pipeline",
        "algorithm",
    ]

    for term in forbidden_terms:
        if term in lowered:
            return False, (
                "This lab evaluates judgment, not AI implementation details."
            )

    return True, "Capacity forecasting decision demonstrates sound operational judgment."
