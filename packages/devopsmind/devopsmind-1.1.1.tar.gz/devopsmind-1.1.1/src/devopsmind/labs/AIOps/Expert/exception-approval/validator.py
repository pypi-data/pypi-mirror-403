from pathlib import Path
import re


def validate():
    """
    Validate Expert-level exception approval governance judgment.

    Enforces:
    - Explicit grant or deny decision
    - Recognition that exceptions transfer risk
    - Clear accountability for exception outcomes
    - Rejection of conditional or mitigation framing
    """

    submission_file = Path("exception_approval_review.md")

    if not submission_file.exists():
        return False, "exception_approval_review.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Exception approval review document is empty."

    # ---- required sections ----
    required_sections = [
        "## approval criteria gap",
        "## exception request rationale",
        "## risk and governance impact",
        "## accountability implications",
        "## exception decision",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section}"

    # ---- reject instructional scaffolding ----
    template_markers = [
        "describe which",
        "explain why",
        "evaluate how",
        "state clearly",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Instructional template text must be removed."

    # ---- decision must be explicit ----
    if not any(term in lowered for term in ["grant", "granted", "deny", "denied"]):
        return False, "Exception decision is not explicit."

    # ---- forbid conditional / mitigation framing ----
    forbidden_patterns = [
        r"temporary",
        r"monitor",
        r"mitigate",
        r"retrain",
        r"controls",
        r"safeguard",
        r"revisit",
    ]

    for pattern in forbidden_patterns:
        if re.search(pattern, lowered):
            return False, "Conditional or mitigation-based reasoning detected."

    # ---- forbid ML / tooling framing ----
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

    return True, "Expert-level exception approval governance judgment validated."
