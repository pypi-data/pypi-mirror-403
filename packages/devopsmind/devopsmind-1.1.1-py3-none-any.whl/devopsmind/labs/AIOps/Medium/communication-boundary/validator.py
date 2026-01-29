from pathlib import Path
import re


def validate():
    """
    Validate authority boundaries for AI-assisted incident communication.

    Enforces:
    - Explicit separation between assistance and authorship
    - Human ownership of externally impactful communication
    - No delegation of communication authority to AI
    """

    submission_file = Path("communication-boundary.md")

    if not submission_file.exists():
        return False, "communication-boundary.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Communication boundary document is empty."

    # ---- structural requirements ----
    required_sections = [
        "# ai communication boundary",
        "# mandatory human authorship areas",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section.title()}"

    # ---- reject untouched template ----
    template_markers = [
        "replace this section",
        "define clearly",
        "write in your own words",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Template scaffolding must be replaced."

    # ---- assistance boundary must exist ----
    if "ai" not in lowered or "may" not in lowered:
        return False, "AI assistance boundary is not clearly articulated."

    # ---- authority boundary must exist ----
    if "must not" not in lowered and "cannot" not in lowered:
        return False, "Human authorship boundary is not clearly articulated."

    # ---- detect AI-as-author framing (loose, semantic) ----
    ai_actor_patterns = [
        r"ai\s+(sends|publishes|releases|communicates|notifies|assures)",
        r"messages?\s+(are|will be)\s+generated\s+by\s+ai",
        r"ai\s+(issues|provides)\s+(updates|statements)",
    ]

    for pattern in ai_actor_patterns:
        if re.search(pattern, lowered):
            return False, "AI is framed as the author or issuer of communication."

    # ---- detect delegation of responsibility ----
    if "final human review" in lowered or "human review only" in lowered:
        return False, "Authority is deferred rather than owned."

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

    return True, "Incident communication boundaries validated."
