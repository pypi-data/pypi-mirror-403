import os
import re

def normalize_header(line):
    """Normalize markdown headers like '# Immediate Actions' → 'immediate actions'"""
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    """Detect unchanged guidance or empty sections."""
    guidance_phrases = [
        "declare the severity level",
        "explain why",
        "explain why each action is necessary",
        "who needs to be informed and why",
    ]
    return len(text.strip()) == 0 or any(p in text for p in guidance_phrases)

def has_substance(text, min_words=10):
    """Ensure section contains real master-level reasoning."""
    return len(text.split()) >= min_words

def validate():
    if not os.path.exists("actions.md"):
        return False, "actions.md not found."

    content = open("actions.md").read().lower()
    lines = content.splitlines()

    required_sections = [
        "incident severity",
        "immediate actions",
        "communication plan",
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

    # Ensure sections are completed and substantive
    for section, lines in parts.items():
        text = " ".join(lines)
        if is_placeholder(text):
            return False, f"Section '{section.title()}' has not been completed."
        if not has_substance(text):
            return False, f"Section '{section.title()}' lacks sufficient depth."

    full_text = " ".join(" ".join(v) for v in parts.values())

    # --- Master-level intent checks (VERY loose) ---

    # 1. Severity judgment (not just stating a number)
    severity_signals = [
        "severity",
        "impact",
        "scope",
        "customer",
        "user",
        "business impact",
        "service impact",
    ]
    if not any(sig in full_text for sig in severity_signals):
        return False, "Severity assessment lacks impact-based reasoning."

    # 2. Coordinated action thinking (not just a list)
    action_signals = [
        "stabilize",
        "contain",
        "coordinate",
        "focus on",
        "prioritize",
        "assign",
        "ensure",
        "protect",
    ]
    if not any(sig in full_text for sig in action_signals):
        return False, "Immediate actions do not demonstrate coordinated incident control."

    # 3. Communication intent and audience awareness
    communication_signals = [
        "inform",
        "notify",
        "update",
        "brief",
        "communicate",
        "stakeholder",
        "leadership",
        "team",
        "customer",
    ]
    if not any(sig in full_text for sig in communication_signals):
        return False, "Communication plan lacks audience or intent awareness."

    return True, "Incident commander actions demonstrate master-level leadership."
