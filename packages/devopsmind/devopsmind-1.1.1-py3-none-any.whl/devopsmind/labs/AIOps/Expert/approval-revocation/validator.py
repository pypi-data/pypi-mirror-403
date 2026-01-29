from pathlib import Path
import re


def validate():
    """
    Validate an Expert-level approval revocation decision.

    Enforces:
    - Explicit revocation or continuation decision
    - Evidence-driven risk reassessment
    - Clear, human-owned accountability
    - Absence of deferral or mitigation framing
    """

    submission_file = Path("revocation_review.md")

    if not submission_file.exists():
        return False, "revocation_review.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Approval revocation review document is empty."

    # ---- required sections ----
    required_sections = [
        "## original approval context",
        "## new evidence summary",
        "## risk reassessment",
        "## accountability implications",
        "## revocation decision",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section}"

    # ---- reject untouched instructional scaffolding ----
    template_markers = [
        "describe why",
        "describe the new",
        "evaluate how",
        "explain who",
        "state clearly",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Template guidance must be replaced with a real governance judgment."

    # ---- decision must be explicit ----
    if not any(term in lowered for term in ["revoke", "revoked", "maintain", "maintained"]):
        return False, "Revocation decision is not explicit."

    # ---- forbid deferral or inertia framing ----
    forbidden_patterns = [
        r"wait and see",
        r"monitor",
        r"pilot",
        r"gather more data",
        r"retrain",
        r"adjust later",
        r"revisit",
    ]

    for pattern in forbidden_patterns:
        if re.search(pattern, lowered):
            return False, "Deferred or conditional decision-making detected."

    # ---- forbid tooling / ML framing ----
    forbidden_terms = [
        "model",
        "training",
        "prompt",
        "api",
        "pipeline",
        "accuracy",
    ]

    if any(term in lowered for term in forbidden_terms):
        return False, "Tooling or ML framing detected."

    return True, "Expert-level approval revocation judgment validated."
