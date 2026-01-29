from pathlib import Path


def validate():
    """
    Validate operational judgment for AI-assisted postmortem drafting.

    This validator evaluates authorship, accountability,
    and trust in official incident records.
    """

    submission_file = Path("ownership-statement.md")

    if not submission_file.exists():
        return False, (
            "ownership-statement.md is missing. Record your decision there."
        )

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, (
            "Submission is empty. A written ownership decision is required."
        )

    # Required structure
    for section in ["# decision", "# accountability and ownership"]:
        if section not in lowered:
            return False, (
                "Submission must include Decision and Accountability and Ownership sections."
            )

    # Reject template language
    template_phrases = [
        "record your decision on whether ai should be used",
        "use the questions below to guide your reasoning",
        "do not copy them into your response",
        "write in your own words",
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
        return False, (
            "Decision section must explicitly state YES or NO."
        )

    # Authorship and narrative ownership
    authorship_terms = [
        "author",
        "authorship",
        "narrative",
        "draft",
        "written by",
        "ownership of the record",
    ]

    if not any(term in lowered for term in authorship_terms):
        return False, (
            "Analysis must address who authors the postmortem narrative."
        )

    # Accountability and responsibility
    accountability_terms = [
        "accountab",
        "responsib",
        "owned",
        "ownership",
        "engineer",
        "organization",
    ]

    if not any(term in lowered for term in accountability_terms):
        return False, (
            "Accountability for the postmortem must be explicitly addressed."
        )

    # Trust and credibility
    trust_terms = [
        "trust",
        "credibility",
        "confidence",
        "stakeholder",
        "official record",
    ]

    if not any(term in lowered for term in trust_terms):
        return False, (
            "Impact on trust and credibility must be considered."
        )

    # Reject ML / tooling framing
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
                "This lab evaluates ownership and accountability, not AI implementation details."
            )

    return True, "Postmortem authorship and ownership decision recorded."
