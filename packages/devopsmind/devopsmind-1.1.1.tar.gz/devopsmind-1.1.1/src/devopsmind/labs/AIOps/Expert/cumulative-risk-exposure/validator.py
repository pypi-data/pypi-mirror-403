from pathlib import Path
import re


def validate():
    """
    Validate Expert-level cumulative risk governance judgment.

    Enforces:
    - Recognition of risk accumulation over time
    - Explicit accountability for continued exposure
    - Clear accept / reject decision
    - Absence of mitigation or reset framing
    """

    submission_file = Path("cumulative_risk_review.md")

    if not submission_file.exists():
        return False, "cumulative_risk_review.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Cumulative risk review document is empty."

    # ---- required sections ----
    required_sections = [
        "## incident history overview",
        "## risk accumulation analysis",
        "## accountability implications",
        "## governance threshold assessment",
        "## cumulative risk decision",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section}"

    # ---- reject instructional scaffolding ----
    template_markers = [
        "summarize the history",
        "evaluate how risk",
        "assess whether",
        "state clearly",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Instructional template text must be removed."

    # ---- decision must be explicit ----
    if not any(term in lowered for term in ["acceptable", "unacceptable", "continue", "cease", "stop"]):
        return False, "Cumulative risk decision is not explicit."

    # ---- forbid mitigation / reset framing ----
    forbidden_patterns = [
        r"mitigate",
        r"improve",
        r"monitor",
        r"retrain",
        r"reset",
        r"start over",
        r"future fixes",
    ]

    for pattern in forbidden_patterns:
        if re.search(pattern, lowered):
            return False, "Mitigation or reset-based reasoning detected."

    # ---- forbid ML framing ----
    forbidden_terms = [
        "model",
        "training",
        "prompt",
        "api",
        "accuracy",
        "pipeline",
    ]

    if any(term in lowered for term in forbidden_terms):
        return False, "ML or tooling framing detected."

    return True, "Expert-level cumulative risk governance judgment validated."
