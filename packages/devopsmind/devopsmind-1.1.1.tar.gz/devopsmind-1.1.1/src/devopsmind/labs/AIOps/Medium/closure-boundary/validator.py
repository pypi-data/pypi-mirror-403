from pathlib import Path
import re


def validate():
    """
    Validate authority boundaries for AI-assisted incident closure.

    Enforces:
    - Explicit separation between assessment and closure authority
    - Clear human ownership of incident finality
    - No delegation of closure or resolution declaration to AI
    """

    submission_file = Path("closure-boundary.md")

    if not submission_file.exists():
        return False, "closure-boundary.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Closure boundary document is empty."

    # ---- structural requirements ----
    required_sections = [
        "# ai incident closure boundary",
        "# mandatory human closure decisions",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section.title()}"

    # ---- reject untouched template scaffolding ----
    template_markers = [
        "replace this section",
        "define clearly",
        "use explicit",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Template scaffolding must be replaced."

    # ---- assistance boundary must exist ----
    if "ai" not in lowered or "may" not in lowered:
        return False, "AI assistance boundary is not clearly articulated."

    # ---- authority boundary must exist ----
    if "must not" not in lowered and "cannot" not in lowered:
        return False, "Human closure authority boundary is not clearly articulated."

    # ---- detect AI-as-closure-author framing (loose, semantic) ----
    ai_closure_patterns = [
        r"ai\s+(closes|closed|closing)\s+(the\s+)?incident",
        r"ai\s+(declares|determines|confirms)\s+(resolution|resolved)",
        r"incident\s+(is|was|will be)\s+closed\s+by\s+ai",
        r"ai\s+(decides|finalizes)\s+(closure|resolution)",
    ]

    for pattern in ai_closure_patterns:
        if re.search(pattern, lowered):
            return False, "AI is framed as having incident closure authority."

    # ---- detect deferred ownership (safety theater) ----
    if "reopen" in lowered or "can be reopened" in lowered:
        return False, "Closure authority is deferred rather than owned."

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

    return True, "Incident closure authority boundaries validated."
