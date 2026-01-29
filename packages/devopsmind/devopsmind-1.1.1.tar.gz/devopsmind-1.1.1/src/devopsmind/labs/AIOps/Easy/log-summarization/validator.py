from pathlib import Path


def validate():
    """
    Validate operational judgment regarding AI-based log summarization.

    This validator evaluates evidence integrity,
    accountability, and decision clarity — not verbosity.
    """

    submission_file = Path("evidence-review.md")

    if not submission_file.exists():
        return False, (
            "evidence-review.md is missing. Record your decision there."
        )

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Submission is empty. A written judgment is required."

    # Required structure
    for section in ["# decision", "# evidence considerations"]:
        if section not in lowered:
            return False, (
                "Submission must include Decision and Evidence Considerations sections."
            )

    # Reject template language
    template_phrases = [
        "record your decision on whether ai should be used",
        "use the questions below to guide your reasoning",
        "do not copy them into your response",
        "do not describe implementation details",
    ]

    for phrase in template_phrases:
        if phrase in lowered:
            return False, (
                "Template guidance must be replaced with original reasoning."
            )

    # Explicit YES / NO
    decision_block = lowered.split("# decision", 1)[1]
    if not any(term in decision_block for term in ["yes", "no"]):
        return False, "Decision section must explicitly state YES or NO."

    # Evidence awareness
    evidence_terms = [
        "evidence",
        "ground truth",
        "raw logs",
        "record",
        "forensic",
        "audit",
        "misrepresent",
        "omit",
    ]

    if not any(term in lowered for term in evidence_terms):
        return False, (
            "Justification must address logs as evidence or ground truth."
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
            "Human accountability for interpretation must be explicit."
        )

    # Reject implementation framing
    forbidden_terms = [
        "model",
        "training",
        "prompt",
        "api",
        "nlp",
        "pipeline",
        "accuracy",
    ]

    for term in forbidden_terms:
        if term in lowered:
            return False, (
                "This lab evaluates judgment, not AI implementation details."
            )

    return True, "Evidence-based log summarization decision demonstrates sound judgment."
