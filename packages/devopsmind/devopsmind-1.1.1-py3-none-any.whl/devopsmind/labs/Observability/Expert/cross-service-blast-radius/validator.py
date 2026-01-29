import os
import re

def normalize_header(line):
    """Normalize markdown headers like '## Blast Radius' → 'blast radius'"""
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    """Detect unchanged guidance or empty sections."""
    guidance_phrases = [
        "list directly and indirectly impacted services",
        "describe how impact propagates across services",
        "explain which dependencies amplify risk",
        "describe which services should be protected first",
    ]
    return len(text.strip()) == 0 or any(p in text for p in guidance_phrases)

def has_substance(text, min_words=8):
    """Ensure the section contains real reasoning, not filler."""
    return len(text.split()) >= min_words

def validate():
    if not os.path.exists("incident-analysis.md"):
        return False, "incident-analysis.md not found."

    content = open("incident-analysis.md").read().lower()
    lines = content.splitlines()

    required_sections = [
        "affected services",
        "blast radius",
        "risk assessment",
        "priority considerations",
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

    # Ensure all required sections exist
    for section in required_sections:
        if section not in parts:
            return False, f"Missing section: {section.title()}"

    # Ensure sections are completed and not placeholders
    for section, lines in parts.items():
        text = " ".join(lines)
        if is_placeholder(text):
            return False, f"Section '{section.title()}' has not been completed."
        if not has_substance(text):
            return False, f"Section '{section.title()}' lacks sufficient reasoning."

    full_text = " ".join(" ".join(v) for v in parts.values())

    # --- Expert-level intent checks (loose, semantic) ---

    # Must consider more than one service/component
    service_indicators = [
        "service",
        "component",
        "system",
        "upstream",
        "downstream",
        "dependency",
    ]
    if sum(1 for s in service_indicators if s in full_text) < 2:
        return False, "Analysis does not clearly consider multiple services or components."

    # Must explain how impact propagates
    propagation_signals = [
        "propagate",
        "cascade",
        "fan out",
        "spread",
        "dependency",
        "knock-on",
        "chain",
    ]
    if not any(sig in full_text for sig in propagation_signals):
        return False, "Blast radius propagation is not explained."

    # Must show prioritization judgment
    prioritization_signals = [
        "prioritize",
        "protect",
        "focus on",
        "first",
        "most important",
        "critical",
        "stabilize",
    ]
    if not any(sig in full_text for sig in prioritization_signals):
        return False, "Service prioritization is not clearly reasoned."

    return True, "Cross-service blast radius analysis demonstrates expert-level judgment."
