from pathlib import Path
import re


def validate():
    """
    Validate Expert-level auditability and defensibility judgment.

    Enforces:
    - Explicit auditability decision
    - Accountability ownership under opacity
    - Rejection of remediation or tooling escape framing
    """

    submission_file = Path("auditability_review.md")

    if not submission_file.exists():
        return False, "auditability_review.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Auditability review document is empty."

    # ---- required sections ----
    required_sections = [
        "## decision recording overview",
        "## post-incident reconstruction feasibility",
        "## accountability exposure",
        "## governance and audit risk",
        "## auditability decision",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section}"

    # ---- reject instructional scaffolding ----
    template_markers = [
        "describe how",
        "evaluate whether",
        "explain who",
        "assess organizational risk",
        "state clearly",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Instructional template text must be removed."

    # ---- decision must be explicit ----
    if not any(term in lowered for term in ["acceptable", "unacceptable", "restrict", "remove", "continue"]):
        return False, "Auditability decision is not explicit."

    # ---- forbid remediation or future fixes ----
    forbidden_patterns = [
        r"add logs",
        r"improve logging",
        r"explainability",
        r"monitor",
        r"retrain",
        r"instrument",
        r"fix later",
    ]

    for pattern in forbidden_patterns:
        if re.search(pattern, lowered):
            return False, "Remediation or tooling-based reasoning detected."

    # ---- forbid ML framing ----
    forbidden_terms = [
        "model",
        "training",
        "prompt",
        "api",
        "accuracy",
    ]

    if any(term in lowered for term in forbidden_terms):
        return False, "ML or tooling framing detected."

    return True, "Expert-level auditability and defensibility judgment validated."
