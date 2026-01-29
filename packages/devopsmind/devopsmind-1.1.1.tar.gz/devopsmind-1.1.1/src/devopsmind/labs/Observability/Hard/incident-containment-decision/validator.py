import os
import re

def normalize_header(line):
    """
    Normalize markdown headers like '## Situation Overview' → 'situation overview'
    """
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    """
    Detect unchanged template placeholders or empty sections.
    """
    placeholders = [
        "summarize",
        "describe actions",
        "describe actions that should wait",
        "explain why",
        "using evidence",
        "given uncertainty",
    ]
    return len(text.strip()) == 0 or any(p in text for p in placeholders)

def validate():
    if not os.path.exists("decision-log.md"):
        return False, "decision-log.md not found."

    content = open("decision-log.md").read().lower()
    lines = content.splitlines()

    required_sections = [
        "situation overview",
        "immediate actions",
        "deferred actions",
        "rationale",
    ]

    parts = {}
    current = None

    for line in lines:
        header = normalize_header(line)
        if header in required_sections:
            current = header
            parts[current] = []
        elif current:
            parts[current].append(line.strip())

    # Ensure all sections exist
    for section in required_sections:
        if section not in parts:
            return False, f"Missing section: {section.title()}"

    # Ensure sections are not left as template placeholders
    for section, lines in parts.items():
        text = " ".join(lines)
        if is_placeholder(text):
            return False, f"Section '{section.title()}' has not been completed."

    full_text = " ".join(
        " ".join(lines) for lines in parts.values()
    )

    # Must distinguish immediate vs deferred actions
    if not any(word in " ".join(parts["deferred actions"]) for word in ["defer", "wait", "later", "after"]):
        return False, "Deferred actions are not clearly identified."

    # Must avoid premature root cause fixing
    forbidden = ["root cause fix", "deploy change", "code change"]
    if any(word in full_text for word in forbidden):
        return False, "Decision includes premature fix actions."

    # Must show containment / safety intent
    if not any(
        word in full_text
        for word in ["reduce impact", "limit", "contain", "stabilize", "prevent escalation"]
    ):
        return False, "Containment intent is not clearly stated."

    return True, "Containment decisions under uncertainty demonstrated."
