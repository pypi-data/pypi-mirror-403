from pathlib import Path
import re


def validate():
    """
    Validate Expert-level go/no-go release judgment.

    Enforces:
    - Explicit go or no-go decision
    - Recognition of uncertainty at release time
    - Clear accountability for release outcomes
    - Defensibility under post-incident review
    """

    submission_file = Path("go_no_go_review.md")

    if not submission_file.exists():
        return False, "go_no_go_review.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Go / no-go review document is empty."

    # ---- required sections ----
    required_sections = [
        "## system readiness overview",
        "## known risks and uncertainty",
        "## accountability implications",
        "## go / no-go decision",
        "## decision defensibility",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section}"

    # ---- reject instructional scaffolding ----
    template_markers = [
        "describe the system",
        "identify known risks",
        "explain who",
        "state clearly",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Instructional template text must be removed."

    # ---- decision must be explicit ----
    if not any(term in lowered for term in ["go", "no-go"]):
        return False, "Go / no-go decision is not explicit."

    # ---- forbid deferred release logic ----
    forbidden_patterns = [
        r"canary",
        r"phased",
        r"monitor",
        r"test more",
        r"retrain",
        r"revisit",
    ]

    for pattern in forbidden_patterns:
        if re.search(pattern, lowered):
            return False, "Deferred or conditional release reasoning detected."

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

    return True, "Expert-level go/no-go release judgment validated."
