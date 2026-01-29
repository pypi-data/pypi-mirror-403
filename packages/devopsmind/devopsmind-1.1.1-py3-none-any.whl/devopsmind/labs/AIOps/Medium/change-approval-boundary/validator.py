from pathlib import Path
import re


def validate():
    """
    Validate authority boundaries for AI-assisted change approval.

    Enforces:
    - Explicit separation between analysis and approval authority
    - Clear human ownership of risk acceptance
    - No delegation of approval or authorization to AI
    """

    submission_file = Path("change-approval-boundary.md")

    if not submission_file.exists():
        return False, "change-approval-boundary.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Change approval boundary document is empty."

    # ---- structural requirements ----
    required_sections = [
        "# ai change approval boundary",
        "# mandatory human approval points",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section.title()}"

    # ---- reject untouched template scaffolding ----
    template_markers = [
        "define clearly",
        "use explicit",
        "replace this section",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Template scaffolding must be replaced."

    # ---- assistance boundary must exist ----
    if "ai" not in lowered or "may" not in lowered:
        return False, "AI assistance boundary is not clearly articulated."

    # ---- authority boundary must exist ----
    if "must not" not in lowered and "cannot" not in lowered:
        return False, "Human approval authority boundary is not clearly articulated."

    # ---- detect AI-as-approver framing (loose, semantic) ----
    ai_approval_patterns = [
        r"ai\s+(approves|approved|approving)\s+(the\s+)?change",
        r"ai\s+(authorizes|authorised|authorizing)",
        r"ai\s+(accepts|accepted)\s+(risk|the\s+risk)",
        r"change\s+(is|was|will be)\s+approved\s+by\s+ai",
        r"ai\s+(decides|determines)\s+(approval|whether\s+to\s+approve)",
    ]

    for pattern in ai_approval_patterns:
        if re.search(pattern, lowered):
            return False, "AI is framed as having approval or risk acceptance authority."

    # ---- detect deferred ownership (approval safety theater) ----
    if "post-change review" in lowered or "review after approval" in lowered:
        return False, "Risk acceptance is deferred rather than owned."

    if "final human review" in lowered:
        return False, "Human authority is described as a fallback, not ownership."

    # ---- forbid ML / tooling framing ----
    forbidden_terms = [
        "model",
        "training",
        "prompt",
        "api",
        "pipeline",
        "accuracy",
        "confidence",
    ]

    if any(term in lowered for term in forbidden_terms):
        return False, "Tooling or ML framing detected."

    return True, "Change approval authority boundaries validated."
