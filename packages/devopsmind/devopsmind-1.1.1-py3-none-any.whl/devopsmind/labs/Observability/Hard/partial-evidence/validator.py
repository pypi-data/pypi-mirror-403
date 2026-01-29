import os
import re

def normalize_header(line):
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    """
    Detects untouched template placeholders.
    """
    placeholders = [
        "describe",
        "list key",
        "explain",
        "describe preventive",
        "using available evidence",
        "based on evidence",
        "observability improvements",
    ]
    return any(p in text for p in placeholders) or len(text.strip()) == 0

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

    root_cause = " ".join(parts["root cause"])

    # Must explain causality OR explicitly state uncertainty
    if not any(
        phrase in root_cause
        for phrase in [
            "because",
            "due to",
            "caused by",
            "cannot conclude",
            "cannot be determined",
            "insufficient data",
            "uncertain",
        ]
    ):
        return False, (
            "Root cause must explain causality or explicitly acknowledge uncertainty "
            "due to missing evidence."
        )

    # Must not invent missing signals
    forbidden = ["gc", "disk", "dependency"]
    if any(word in root_cause for word in forbidden):
        return False, "Root cause references signals not present in evidence."

    corrective = " ".join(parts["corrective actions"])

    # Corrective actions must include observability improvement
    if not any(
        phrase in corrective
        for phrase in [
            "monitor",
            "add metric",
            "improve visibility",
            "instrument",
            "observability",
        ]
    ):
        return False, "Corrective actions must address observability gaps."

    return True, "Disciplined RCA under partial observability demonstrated."
