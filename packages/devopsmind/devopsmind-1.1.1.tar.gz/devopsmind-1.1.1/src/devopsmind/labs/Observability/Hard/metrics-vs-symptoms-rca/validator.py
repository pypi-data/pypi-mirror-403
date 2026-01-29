import os
import re

def normalize_header(line):
    """Normalize markdown headers to plain section names."""
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    """Detect unchanged guidance text or empty sections."""
    placeholders = [
        "describe what happened",
        "list key metric changes",
        "explain the underlying cause",
        "not the symptoms",
        "describe actions to prevent",
        "without implementation detail",
        "based on evidence",
        "with timestamps",
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

    # -------------------------------------------------
    # Root cause precision checks
    # -------------------------------------------------
    root_cause_text = " ".join(parts["root cause"])

    # Must explain *why*
    if not any(
        word in root_cause_text
        for word in ["because", "due to", "caused by", "resulted from", "led to"]
    ):
        return False, "Root cause does not explain causality."

    # Must not restate symptoms only
    symptom_words = ["latency", "slow", "timeout"]
    if any(word in root_cause_text for word in symptom_words) and not any(
        m in root_cause_text for m in ["memory", "cpu", "gc", "resource"]
    ):
        return False, "Root cause describes symptoms without identifying underlying cause."

    # -------------------------------------------------
    # Timeline precision checks
    # -------------------------------------------------
    timeline_text = " ".join(parts["timeline"])

    if not re.search(r"\b\d{2}:\d{2}\b", timeline_text):
        return False, "Timeline must include time-based events (HH:MM)."

    # -------------------------------------------------
    # Corrective actions must be preventive
    # -------------------------------------------------
    corrective_text = " ".join(parts["corrective actions"])

    if not any(
        word in corrective_text
        for word in ["prevent", "reduce", "avoid", "monitor", "instrument", "observe"]
    ):
        return False, "Corrective actions do not focus on prevention."

    return True, "Root cause analysis distinguishes metrics from symptoms correctly."
