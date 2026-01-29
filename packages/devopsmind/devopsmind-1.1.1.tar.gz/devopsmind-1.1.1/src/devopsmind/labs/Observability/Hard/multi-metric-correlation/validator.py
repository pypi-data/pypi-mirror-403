import os
import re

def normalize_header(line):
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    placeholders = [
        "describe the observed impact",
        "list key metric changes",
        "explain which metric behavior",
        "describe preventive actions",
        "using metrics",
        "with timestamps",
        "based on the identified cause",
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

        # Start collecting only when a required section is found
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

    # Must explain causality
    if not any(
        word in root_cause
        for word in ["because", "due to", "caused by", "led to", "resulted from"]
    ):
        return False, "Root cause does not explain causality."

    # Must reference multiple metrics
    metric_refs = ["memory", "gc", "cpu", "latency"]
    referenced = [m for m in metric_refs if m in root_cause]

    if len(referenced) < 2:
        return False, "Root cause does not correlate multiple metrics."

    # Must not describe symptoms only
    if "latency" in root_cause and all(
        m not in root_cause for m in ["memory", "gc", "cpu"]
    ):
        return False, "Root cause focuses on symptoms without underlying cause."

    corrective = " ".join(parts["corrective actions"])

    # Corrective actions must be preventive / observability-oriented
    if not any(
        word in corrective
        for word in ["prevent", "reduce", "monitor", "limit", "instrument", "observe"]
    ):
        return False, "Corrective actions are not preventive or observability-focused."

    return True, "Multi-metric correlation and precise RCA demonstrated."
