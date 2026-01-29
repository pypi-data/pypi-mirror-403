import os
import re

def normalize_header(line):
    """Normalize markdown headers like '## Risk Ownership' → 'risk ownership'"""
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    """Detect unchanged guidance or empty sections."""
    guidance_phrases = [
        "summarize the incident",
        "current impact",
        "describe the action",
        "what makes it irreversible",
        "state clearly whether you proceed",
        "explicitly state which risks you accept",
        "describe consequences",
        "required follow-up actions",
    ]
    return len(text.strip()) == 0 or any(p in text for p in guidance_phrases)

def has_substance(text, min_words=8):
    """Ensure section contains real reasoning."""
    return len(text.split()) >= min_words

def validate():
    if not os.path.exists("risk-ownership.md"):
        return False, "risk-ownership.md not found."

    content = open("risk-ownership.md").read().lower()
    lines = content.splitlines()

    required_sections = [
        "situation overview",
        "proposed irreversible action",
        "decision",
        "risk ownership",
        "consequences and follow-up",
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

    # Ensure sections are completed and meaningful
    for section, lines in parts.items():
        text = " ".join(lines)
        if is_placeholder(text):
            return False, f"Section '{section.title()}' has not been completed."
        if not has_substance(text):
            return False, f"Section '{section.title()}' lacks sufficient reasoning."

    full_text = " ".join(" ".join(v) for v in parts.values())

    # --- Expert intent checks (NOT keyword-tight) ---

    # 1. Must make a clear decision (yes / no / proceed / stop)
    decision_signals = [
        "we will",
        "we will not",
        "i will",
        "i will not",
        "proceed",
        "do not proceed",
        "refuse",
        "decline",
        "move forward",
        "halt",
    ]
    if not any(sig in full_text for sig in decision_signals):
        return False, "A clear irreversible decision is not stated."

    # 2. Must acknowledge irreversibility (one-way nature)
    irreversibility_signals = [
        "cannot undo",
        "cannot be undone",
        "one-way",
        "permanent",
        "no rollback",
        "cannot revert",
        "irreversible",
    ]
    if not any(sig in full_text for sig in irreversibility_signals):
        return False, "Irreversible nature of the action is not acknowledged."

    # 3. Must show risk ownership (explicit responsibility)
    ownership_signals = [
        "i accept",
        "we accept",
        "i am responsible",
        "we are responsible",
        "own the risk",
        "take responsibility",
        "accountable for",
    ]
    if not any(sig in full_text for sig in ownership_signals):
        return False, "Risk ownership is not clearly stated."

    # 4. Must acknowledge consequences and follow-up
    consequence_signals = [
        "consequence",
        "impact",
        "risk",
        "follow-up",
        "monitor",
        "review",
        "mitigate",
        "watch",
    ]
    if not any(sig in full_text for sig in consequence_signals):
        return False, "Consequences and follow-up actions are not acknowledged."

    return True, "Irreversible decision made with explicit risk ownership and accountability."
