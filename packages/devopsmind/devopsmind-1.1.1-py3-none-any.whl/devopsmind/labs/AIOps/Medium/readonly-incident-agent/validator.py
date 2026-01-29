from pathlib import Path
import re


def validate():
    """
    Validate a read-only AIOps agent design.

    Enforces:
    - Read-only capability boundaries
    - Absence of execution or remediation authority
    - Explicit human ownership of decisions
    """

    submission_file = Path("agent_design.md")

    if not submission_file.exists():
        return False, "agent_design.md is missing."

    content = submission_file.read_text(encoding="utf-8").strip()
    lowered = content.lower()

    if not content:
        return False, "Agent design document is empty."

    # ---- required sections ----
    required_sections = [
        "# read-only incident analysis agent design",
        "## agent purpose",
        "## allowed observations",
        "## boundaries",
        "## human authority",
    ]

    for section in required_sections:
        if section not in lowered:
            return False, f"Missing required section: {section}"

    # ---- reject template scaffolding ----
    template_markers = [
        "replace this section",
        "clear statement",
        "description of the types",
    ]

    if any(marker in lowered for marker in template_markers):
        return False, "Template scaffolding must be replaced."

    # ---- forbid action / execution capability ----
    forbidden_actions = [
        "restart",
        "deploy",
        "scale",
        "delete",
        "execute",
        "apply",
        "modify",
        "change configuration",
        "take action",
    ]

    for action in forbidden_actions:
        if re.search(rf"\b{action}\b", lowered):
            return False, "Design permits operational action."

    # ---- forbid implicit decision authority ----
    authority_leaks = [
        r"ai\s+(decides|determines|confirms|resolves)",
        r"agent\s+(decides|acts|initiates)",
        r"automatically\s+(resolve|fix|remediate)",
    ]

    for pattern in authority_leaks:
        if re.search(pattern, lowered):
            return False, "Agent is framed as having decision or resolution authority."

    # ---- require explicit read-only boundary ----
    if "read-only" not in lowered and "cannot act" not in lowered:
        return False, "Read-only boundary is not explicitly stated."

    # ---- require human ownership ----
    if "human" not in lowered:
        return False, "Human authority and accountability are not explicitly stated."

    # ---- forbid tooling / ML framing ----
    forbidden_terms = [
        "model",
        "training",
        "prompt",
        "api",
        "pipeline",
        "confidence score",
    ]

    if any(term in lowered for term in forbidden_terms):
        return False, "Tooling or ML framing detected."

    return True, "Read-only agent boundaries validated."
