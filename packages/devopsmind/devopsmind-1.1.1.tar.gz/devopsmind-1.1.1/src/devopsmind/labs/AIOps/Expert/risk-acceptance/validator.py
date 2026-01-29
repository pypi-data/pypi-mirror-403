from pathlib import Path
import re


def validate():
    """
    Validate Expert-level organizational risk acceptance judgment.

    Enforces:
    - Explicit accept or reject decision
    - Recognition that accepted risk persists
    - Clear accountability for consequences
    - Absence of mitigation or control framing
    """

    submission_file = Path("risk_acceptance_review.md")

    if not submission_file.exists():
        return False, "risk_acceptance_review.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Risk acceptance review document is empty."

    # ---- required sections ----
    required_sections = [
        "## system and risk overview",
        "## risk severity and exposure",
        "## accountability implications",
        "## risk acceptance decision",
        "## decision defensibility",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section}"

    # ---- reject instructional scaffolding ----
    template_markers = [
        "describe the ai system",
        "evaluate the potential impact",
        "explain who is accountable",
        "state clearly",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Instructional template text must be removed."

    # ---- decision must be explicit ----
    if not any(term in lowered for term in ["accept", "accepted", "reject", "rejected"]):
        return False, "Risk acceptance decision is not explicit."

    # ---- forbid mitigation / control framing ----
    forbidden_patterns = [
        r"mitigate",
        r"reduce risk",
        r"monitor",
        r"retrain",
        r"controls",
        r"safeguard",
        r"fix later",
    ]

    for pattern in forbidden_patterns:
        if re.search(pattern, lowered):
            return False, "Mitigation or control-based reasoning detected."

    # ---- forbid ML framing ----
    forbidden_terms = [
        "model",
        "training",
        "prompt",
        "api",
        "pipeline",
        "accuracy",
    ]

    if any(term in lowered for term in forbidden_terms):
        return False, "ML or tooling framing detected."

    return True, "Expert-level organizational risk acceptance judgment validated."
