import os
import re

def normalize_header(line):
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    placeholders = [
        "describe what happened",
        "hh:mm",
        "event",
        "explain the primary cause",
        "focus on",
        "list concrete steps",
    ]
    return len(text.strip()) == 0 or any(p in text.lower() for p in placeholders)

def validate():
    if not os.path.exists("rca.md"):
        return False, "rca.md not found."

    content = open("rca.md").read()
    lines = content.splitlines()

    required_sections = [
        "incident summary",
        "timeline",
        "root cause",
        "corrective actions"
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

    # Ensure sections are not left as guidance
    for section, lines in parts.items():
        text = " ".join(lines)
        if is_placeholder(text):
            return False, f"Section '{section.title()}' has not been completed."

    root_cause = " ".join(parts["root cause"]).lower()

    # Root cause must mention memory explicitly
    if "memory" not in root_cause:
        return False, "Root cause analysis must explicitly mention memory."

    timeline = " ".join(parts["timeline"])

    # Timeline must contain time-based entries (HH:MM)
    if not re.search(r"\b\d{2}:\d{2}\b", timeline):
        return False, "Timeline must include time-based events (HH:MM)."

    return True, "Guided RCA completed with proper reasoning."
