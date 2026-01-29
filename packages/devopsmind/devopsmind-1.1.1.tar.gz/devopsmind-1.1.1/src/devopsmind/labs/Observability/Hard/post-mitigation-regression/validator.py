import os
import re

def normalize_header(line):
    """Normalize markdown headers like '## Root Cause' → 'root cause'"""
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    """Detect unchanged guidance or empty sections."""
    placeholders = [
        "describe the initial incident",
        "identify stabilization",
        "explain why the issue reappeared",
        "after mitigation",
        "with evidence",
        "describe actions to prevent recurrence",
        "including validation of mitigation",
    ]
    return len(text.strip()) == 0 or any(p in text for p in placeholders)

def validate():
    if not os.path.exists("rca.md"):
        return False, "rca.md not found."

    content = open("rca.md").read().lower()
    lines = content.splitlines()

    required_sections = [
        "incident summary",
        "timeline",
        "root cause",
        "corrective actions",
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

    full_text = " ".join(" ".join(v) for v in parts.values())

    # Must mention mitigation
    if "mitigation" not in full_text:
        return False, "Mitigation is not discussed."

    # Must identify regression after mitigation
    if not any(word in full_text for word in ["regression", "reappeared", "returned", "recurred"]):
        return False, "Regression after mitigation is not identified."

    # Root cause must explain WHY regression occurred
    root_cause_text = " ".join(parts["root cause"])

    if not any(
        word in root_cause_text
        for word in ["because", "due to", "caused by", "resulted from"]
    ):
        return False, "Root cause does not explain why the regression occurred."

    return True, "Post-mitigation regression correctly analyzed."
