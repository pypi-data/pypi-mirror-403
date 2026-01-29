from pathlib import Path


def validate():
    """
    Validate operational judgment for AI-based incident classification.

    This validator evaluates accountability, risk awareness,
    and clarity of decision — not verbosity or implementation detail.
    """

    submission_file = Path("decision.md")

    if not submission_file.exists():
        return False, (
            "decision.md is missing. Record your incident classification decision there."
        )

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Submission is empty. A written judgment is required."

    # Required structure
    for section in ["# decision", "# justification"]:
        if section not in lowered:
            return False, (
                "Submission must include Decision and Justification sections."
            )

    # Reject template language
    template_phrases = [
        "record your decision regarding the use of ai",
        "choose one position and state it clearly",
        "use the questions below to guide your thinking",
        "write in your own words",
        "do not describe implementation details",
    ]

    for phrase in template_phrases:
        if phrase in lowered:
            return False, (
                "Template guidance must be replaced with original operational reasoning."
            )

    # Explicit YES / NO decision
    decision_block = lowered.split("# decision", 1)[1]
    if not any(term in decision_block for term in ["yes", "no"]):
        return False, (
            "Decision section must explicitly state YES or NO."
        )

    # Risk awareness
    risk_terms = [
        "risk",
        "misclass",
        "delay",
        "suppressed",
        "escalation",
        "urgency",
        "silent",
        "impact",
    ]

    if not any(term in lowered for term in risk_terms):
        return False, (
            "Justification must address misclassification risk and operational impact."
        )

    # Accountability
    accountability_terms = [
        "human",
        "engineer",
        "on-call",
        "accountab",
        "responsib",
        "owned",
    ]

    if not any(term in lowered for term in accountability_terms):
        return False, (
            "Human accountability for classification decisions must be explicit."
        )

    # Reject implementation framing
    forbidden_terms = [
        "model",
        "training",
        "prompt",
        "api",
        "pipeline",
        "fine-tuning",
    ]

    for term in forbidden_terms:
        if term in lowered:
            return False, (
                "This lab evaluates judgment, not AI implementation details."
            )

    return True, "Incident classification decision demonstrates sound operational judgment."
