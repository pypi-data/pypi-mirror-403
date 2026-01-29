from pathlib import Path
import re


def validate():
    """
    Validate authority boundaries for AI-assisted incident resolution.

    Enforces:
    - Explicit separation between advice and action
    - Clear human ownership of system-changing decisions
    - No delegation of execution or resolution authority to AI
    """

    submission_file = Path("resolution-boundary.md")

    if not submission_file.exists():
        return False, "resolution-boundary.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Resolution boundary document is empty."

    # ---- structural requirements ----
    required_sections = [
        "# ai resolution boundary",
        "# mandatory human control points",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section.title()}"

    # ---- reject untouched template scaffolding ----
    template_markers = [
        "define clearly",
        "use explicit language",
        "replace this section",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Template scaffolding must be replaced."

    # ---- assistance boundary must exist ----
    if "ai" not in lowered or "may" not in lowered:
        return False, "AI assistance boundary is not clearly articulated."

    # ---- human control boundary must exist ----
    if "must not" not in lowered and "cannot" not in lowered:
        return False, "Human action control boundary is not clearly articulated."

    # ---- detect AI-as-actor framing (loose, semantic) ----
    ai_action_patterns = [
        r"ai\s+(restarts|restarted|restarting)",
        r"ai\s+(rolls\s+back|rollback|rolled\s+back)",
        r"ai\s+(executes|executed|executing)",
        r"ai\s+(applies|applied|applying)",
        r"ai\s+(changes|modifies|updates)\s+(config|configuration|state)",
        r"incident\s+(is|was|will be)\s+resolved\s+by\s+ai",
        r"ai\s+(fixes|resolves|mitigates)",
    ]

    for pattern in ai_action_patterns:
        if re.search(pattern, lowered):
            return False, "AI is framed as performing or triggering resolution actions."

    # ---- detect deferred ownership / safety theater ----
    if "post-action review" in lowered or "review after action" in lowered:
        return False, "Action authority is deferred rather than owned."

    if "automatically" in lowered and "human" not in lowered:
        return False, "Automation is implied without explicit human control."

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

    return True, "Incident resolution action boundaries validated."
