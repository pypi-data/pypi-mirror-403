from pathlib import Path
import re


def validate():
    """
    Validate operational judgment for AI-based alert deduplication.

    This validator enforces clarity of decision, risk awareness,
    and preservation of human accountability.
    """

    submission_file = Path("alert-risk-assessment.md")

    if not submission_file.exists():
        return False, (
            "alert-risk-assessment.md is missing. "
            "Record your operational decision in that file."
        )

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Submission is empty. A written judgment is required."

    # Required headings
    for section in ["# decision", "# risk assessment"]:
        if section not in lowered:
            return False, (
                "Submission must include both Decision and Risk Assessment sections."
            )

    # Reject template language
    forbidden_templates = [
        "record your decision",
        "use the questions below",
        "do not copy them into your answer",
        "write in your own words",
        "do not describe implementation details",
    ]

    for phrase in forbidden_templates:
        if phrase in lowered:
            return False, (
                "Template guidance must be replaced with original operational reasoning."
            )

    # Require explicit decision
    decision_block = lowered.split("# decision", 1)[1]
    if not any(term in decision_block for term in ["yes", "no"]):
        return False, (
            "Decision section must explicitly state YES or NO."
        )

    # Risk awareness signals
    risk_terms = [
        "risk",
        "visibility",
        "missed",
        "hidden",
        "suppressed",
        "situational awareness",
        "delay",
        "impact",
    ]

    if not any(term in lowered for term in risk_terms):
        return False, (
            "Risk assessment does not demonstrate awareness of visibility or operational risk."
        )

    # Accountability check
    accountability_terms = [
        "human",
        "engineer",
        "on-call",
        "responsib",
        "accountab",
        "owned",
    ]

    if not any(term in lowered for term in accountability_terms):
        return False, (
            "Human accountability is not clearly stated."
        )

    # Reject implementation framing
    forbidden_terms = [
        "model",
        "training",
        "prompt",
        "api",
        "nlp",
        "clustering",
        "algorithm",
    ]

    for term in forbidden_terms:
        if term in lowered:
            return False, (
                "This lab evaluates judgment, not AI implementation details."
            )

    return True, "Alert deduplication decision demonstrates sound operational judgment."
