from pathlib import Path
import re


def validate():
    """
    Validate Expert-level production approval judgment.

    Enforces:
    - Explicit approve / reject decision
    - Clear ownership of risk and accountability
    - Recognition that approval accepts ongoing exposure
    - Absence of mitigation, redesign, or tooling framing
    """

    submission_file = Path("approval_review.md")

    if not submission_file.exists():
        return False, "approval_review.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Approval review document is empty."

    # ---- required structural sections ----
    required_sections = [
        "# system overview",
        "# risk identification",
        "# risk acceptability assessment",
        "# accountability implications",
        "# approval decision",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section}"

    # ---- reject instructional scaffolding ----
    template_markers = [
        "describe the ai system",
        "identify the primary",
        "evaluate whether",
        "explain who becomes accountable",
        "state clearly whether",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Instructional template text must be removed."

    # ---- approval decision must be explicit ----
    if not any(term in lowered for term in ["approve", "approved", "reject", "rejected"]):
        return False, "Approval decision is not explicit."

    # ---- forbid mitigation / control framing ----
    forbidden_reasoning = [
        r"mitigate",
        r"monitor",
        r"retrain",
        r"controls?",
        r"safeguard",
        r"fix later",
        r"improve later",
        r"reduce risk",
    ]

    for pattern in forbidden_reasoning:
        if re.search(pattern, lowered):
            return False, "Mitigation or control-based reasoning detected."

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

    return True, "Expert-level production approval judgment validated."
