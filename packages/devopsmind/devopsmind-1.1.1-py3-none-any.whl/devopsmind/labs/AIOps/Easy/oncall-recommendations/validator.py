from pathlib import Path


def validate():
    """
    Validate operational judgment for AI recommendations to on-call engineers.

    This validator evaluates authority boundaries,
    automation bias awareness, and responsibility ownership.
    """

    submission_file = Path("trust-boundary.md")

    if not submission_file.exists():
        return False, (
            "trust-boundary.md is missing. Record your decision there."
        )

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, (
            "Submission is empty. A written trust boundary decision is required."
        )

    # Required structure
    for section in ["# decision", "# trust and responsibility"]:
        if section not in lowered:
            return False, (
                "Submission must include Decision and Trust and Responsibility sections."
            )

    # Reject template language
    template_phrases = [
        "record your decision on whether ai should be allowed",
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

    # Influence and automation bias awareness
    influence_terms = [
        "influence",
        "bias",
        "pressure",
        "stress",
        "defer",
        "authority",
        "cannot be ignored",
    ]

    if not any(term in lowered for term in influence_terms):
        return False, (
            "Analysis must address how recommendations influence human behavior under pressure."
        )

    # Responsibility and accountability
    responsibility_terms = [
        "accountab",
        "responsib",
        "owned",
        "engineer",
        "human",
        "decision rests",
    ]

    if not any(term in lowered for term in responsibility_terms):
        return False, (
            "Human responsibility for actions must be explicitly acknowledged."
        )

    # Reject tooling / ML framing
    forbidden_terms = [
        "model",
        "training",
        "prompt",
        "api",
        "accuracy",
        "pipeline",
    ]

    for term in forbidden_terms:
        if term in lowered:
            return False, (
                "This lab evaluates judgment and authority, not AI implementation details."
            )

    return True, "On-call recommendation trust boundary decision recorded."
