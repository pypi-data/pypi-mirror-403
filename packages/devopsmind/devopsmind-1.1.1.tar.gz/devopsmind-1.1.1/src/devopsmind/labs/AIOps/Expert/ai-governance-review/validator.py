from pathlib import Path
import re


def validate():
    """
    Validate an enterprise AIOps governance review.

    This validator enforces:
    - Explicit governance outcome
    - Defensible scope and risk framing
    - Clear, human-owned accountability
    - Auditability under failure conditions

    It does not evaluate writing quality or length.
    """

    submission_file = Path("governance_review.md")

    if not submission_file.exists():
        return False, "governance_review.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Governance review document is empty."

    # ---- required sections (structure, not content) ----
    required_sections = [
        "## decision",
        "## scope",
        "## risk assessment",
        "## accountability",
        "## audit & traceability",
        "## conditions",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section}"

    # ---- reject untouched template scaffolding ----
    template_markers = [
        "state the governance decision",
        "define where the aiops system",
        "identify material risks",
        "describe how decisions",
        "list enforceable conditions",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Template guidance must be replaced with an actual governance review."

    # ---- governance decision must be explicit ----
    if not any(term in lowered for term in ["approved", "rejected"]):
        return False, "Governance outcome is not explicitly stated."

    # ---- accountability must be human-owned ----
    abdication_patterns = [
        r"shared responsibility",
        r"collective ownership",
        r"no single owner",
        r"ai is responsible",
        r"system is responsible",
    ]

    for pattern in abdication_patterns:
        if re.search(pattern, lowered):
            return False, "Accountability is ambiguous or abdicated."

    # ---- forbid unsafe governance framing ----
    forbidden_phrases = [
        "fully autonomous",
        "self-healing",
        "no human approval",
        "automatic remediation",
    ]

    for phrase in forbidden_phrases:
        if phrase in lowered:
            return False, f"Unsafe governance framing detected: {phrase}"

    # ---- auditability must be addressed ----
    if not any(term in lowered for term in ["audit", "trace", "log", "reviewable"]):
        return False, "Auditability and traceability are not addressed."

    return True, "Enterprise AIOps governance review validated."
