from pathlib import Path
import re


def validate():
    """
    Validate an Expert-level governance precedent review.

    Enforces:
    - Explicit precedent decision
    - Forward-looking governance reasoning
    - Clear accountability ownership
    - Absence of conditional or mitigation-based approval logic

    Does not evaluate length, style, or optimism.
    """

    submission_file = Path("precedent_review.md")

    if not submission_file.exists():
        return False, "precedent_review.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Precedent review document is empty."

    # ---- required sections ----
    required_sections = [
        "## approval context",
        "## precedent analysis",
        "## governance impact",
        "## accountability implications",
        "## precedent decision",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section}"

    # ---- reject untouched instructional scaffolding ----
    template_markers = [
        "describe the ai system",
        "analyze how approving",
        "evaluate how governance",
        "state clearly whether",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Template guidance must be replaced with real judgment."

    # ---- require explicit precedent outcome ----
    if not any(term in lowered for term in ["acceptable", "unacceptable", "approve", "reject"]):
        return False, "Precedent decision is not explicit."

    # ---- forbid conditional / mitigation framing ----
    forbidden_patterns = [
        r"case[-\s]?by[-\s]?case",
        r"exception",
        r"mitigate",
        r"monitor",
        r"retrain",
        r"adjust later",
    ]

    for pattern in forbidden_patterns:
        if re.search(pattern, lowered):
            return False, "Conditional or mitigation-based precedent reasoning detected."

    # ---- require precedent-aware reasoning ----
    if "precedent" not in lowered and "future" not in lowered:
        return False, "Long-term precedent impact is not addressed."

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

    return True, "Expert-level precedent governance judgment validated."
