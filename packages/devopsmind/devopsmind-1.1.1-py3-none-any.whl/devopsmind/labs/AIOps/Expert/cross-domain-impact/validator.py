from pathlib import Path
import re


def validate():
    """
    Validate Expert-level cross-domain governance judgment.

    Enforces:
    - Explicit permit or deny decision
    - Recognition of risk amplification
    - Accountability clarity across domains
    - Rejection of mitigation or staged expansion framing
    """

    submission_file = Path("cross_domain_review.md")

    if not submission_file.exists():
        return False, "cross_domain_review.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Cross-domain review document is empty."

    # ---- required sections ----
    required_sections = [
        "## current domain usage",
        "## proposed cross-domain influence",
        "## risk amplification analysis",
        "## accountability implications",
        "## cross-domain decision",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section}"

    # ---- reject instructional scaffolding ----
    template_markers = [
        "describe where",
        "explain how",
        "evaluate how",
        "state clearly",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Instructional template text must be removed."

    # ---- decision must be explicit ----
    if not any(term in lowered for term in ["permit", "permitted", "deny", "denied"]):
        return False, "Cross-domain decision is not explicit."

    # ---- forbid mitigation / staged expansion ----
    forbidden_patterns = [
        r"pilot",
        r"phase",
        r"gradual",
        r"monitor",
        r"mitigate",
        r"revisit",
        r"adjust later",
    ]

    for pattern in forbidden_patterns:
        if re.search(pattern, lowered):
            return False, "Deferred or mitigation-based reasoning detected."

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

    return True, "Expert-level cross-domain governance judgment validated."
