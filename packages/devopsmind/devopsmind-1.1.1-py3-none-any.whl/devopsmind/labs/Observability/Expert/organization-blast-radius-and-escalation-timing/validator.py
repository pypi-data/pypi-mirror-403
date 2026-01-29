import os
import re

def normalize_header(line):
    """Normalize markdown headers like '## Timing Rationale' → 'timing rationale'"""
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    """Detect unchanged guidance or empty sections."""
    guidance_phrases = [
        "summarize technical and organizational impact",
        "describe which teams and services may be affected",
        "state whether to escalate",
        "explain why this timing",
        "describe risks of escalating",
    ]
    return len(text.strip()) == 0 or any(p in text for p in guidance_phrases)

def has_substance(text, min_words=8):
    """Ensure section contains real reasoning, not filler."""
    return len(text.split()) >= min_words

def validate():
    if not os.path.exists("escalation-analysis.md"):
        return False, "escalation-analysis.md not found."

    content = open("escalation-analysis.md").read().lower()
    lines = content.splitlines()

    required_sections = [
        "current situation",
        "potential blast radius",
        "escalation decision",
        "timing rationale",
        "risks of this decision",
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

    # Ensure sections are completed and not placeholders
    for section, lines in parts.items():
        text = " ".join(lines)
        if is_placeholder(text):
            return False, f"Section '{section.title()}' has not been completed."
        if not has_substance(text):
            return False, f"Section '{section.title()}' lacks sufficient reasoning."

    # Combine all text for high-level reasoning checks
    full_text = " ".join(" ".join(v) for v in parts.values())

    # --- Expert reasoning checks (LOOSE, intent-based) ---

    # Organizational / team impact must be considered
    org_signals = ["team", "organization", "stakeholder", "on-call", "management"]
    if not any(sig in full_text for sig in org_signals):
        return False, "Organizational blast radius is not clearly considered."

    # Must make a clear escalation timing decision
    decision_signals = [
        "escalate",
        "hold",
        "delay",
        "wait",
        "do not escalate",
        "not escalating",
    ]
    if not any(sig in full_text for sig in decision_signals):
        return False, "An explicit escalation timing decision is missing."

    # Must explain *why* that timing was chosen
    rationale_signals = [
        "because",
        "so that",
        "in order to",
        "to avoid",
        "to reduce",
        "to minimize",
    ]
    if not any(sig in full_text for sig in rationale_signals):
        return False, "Escalation timing is not justified with reasoning."

    # Must acknowledge risks or downsides
    risk_signals = [
        "risk",
        "downside",
        "trade-off",
        "impact",
        "cost",
        "disruption",
        "noise",
    ]
    if not any(sig in full_text for sig in risk_signals):
        return False, "Risks or downsides of the escalation decision are not acknowledged."

    return True, "Escalation timing evaluated with expert-level organizational judgment."
