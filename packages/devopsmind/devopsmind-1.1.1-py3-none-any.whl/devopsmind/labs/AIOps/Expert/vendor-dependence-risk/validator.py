from pathlib import Path
import re


def validate():
    """
    Validate Expert-level vendor dependence governance judgment.

    Enforces:
    - Explicit vendor dependence accept / reject decision
    - Clear recognition of loss of operational autonomy
    - Internal accountability despite third-party dependence
    - Absence of mitigation, procurement, or redesign framing
    """

    submission_file = Path("vendor_dependence_review.md")

    if not submission_file.exists():
        return False, "vendor_dependence_review.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Vendor dependence review document is empty."

    # ---- required semantic sections (heading level agnostic) ----
    required_sections = [
        "vendor dependency overview",
        "failure scenario analysis",
        "autonomy and control assessment",
        "accountability implications",
        "vendor dependence decision",
    ]

    for section in required_sections:
        pattern = rf"^\s*#+\s*{re.escape(section)}\s*$"
        if not re.search(pattern, lowered, re.MULTILINE):
            return False, f"Missing required section: {section}"

    # ---- reject instructional scaffolding ----
    template_markers = [
        "describe the ai system",
        "explain how incidents would unfold",
        "evaluate the organization’s ability",
        "state clearly whether",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Instructional template text must be removed."

    # ---- explicit governance decision required ----
    if not any(term in lowered for term in ["acceptable", "unacceptable", "accept", "reject"]):
        return False, "Vendor dependence decision is not explicit."

    # ---- forbid mitigation / procurement framing ----
    forbidden_reasoning = [
        r"\bbackup vendor\b",
        r"\bredundancy\b",
        r"\bcontract\b",
        r"\bsla\b",
        r"\brenegotiate\b",
        r"\bexit strategy\b",
        r"\bmitigate\b",
        r"\bmonitor\b",
    ]

    for pattern in forbidden_reasoning:
        if re.search(pattern, lowered):
            return False, "Mitigation or procurement-based reasoning detected."

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

    return True, "Expert-level vendor dependence governance judgment validated."
