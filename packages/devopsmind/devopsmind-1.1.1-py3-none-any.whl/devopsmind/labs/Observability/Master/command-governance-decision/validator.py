import os
import re

def normalize_header(line):
    """Normalize markdown headers like '## Command Decisions' → 'command decisions'"""
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    """Detect unchanged guidance or empty sections."""
    guidance_phrases = [
        "summarize incident status and impact",
        "identify relevant policies and guardrails",
        "describe leadership and coordination decisions",
        "explain internal and external communication approach",
        "describe risks and how decision ownership is handled",
    ]
    return len(text.strip()) == 0 or any(p in text for p in guidance_phrases)

def has_substance(text, min_words=10):
    """Ensure section contains real command-level reasoning."""
    return len(text.split()) >= min_words

def validate():
    if not os.path.exists("command-decision.md"):
        return False, "command-decision.md not found."

    content = open("command-decision.md").read().lower()
    lines = content.splitlines()

    required_sections = [
        "situation overview",
        "governance constraints",
        "command decisions",
        "communication strategy",
        "risks and accountability",
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

    # --- Master-level intent checks (VERY loose, authority-driven) ---

    # 1. Governance / constraint awareness (policy, guardrails, authority limits)
    governance_signals = [
        "policy",
        "governance",
        "guardrail",
        "approval",
        "authority",
        "compliance",
        "constraint",
        "regulation",
    ]
    if not any(sig in full_text for sig in governance_signals):
        return False, "Governance constraints or authority boundaries are not clearly considered."

    # 2. Command authority and ownership (decision responsibility)
    authority_signals = [
        "decide",
        "decision",
        "direct",
        "authorize",
        "own",
        "ownership",
        "responsible",
        "accountable",
    ]
    if not any(sig in full_text for sig in authority_signals):
        return False, "Command authority or decision ownership is not clearly demonstrated."

    # 3. Communication intent (internal + external awareness)
    communication_signals = [
        "communicate",
        "inform",
        "notify",
        "update",
        "message",
        "brief",
        "stakeholder",
        "public",
        "internal",
        "external",
    ]
    if not any(sig in full_text for sig in communication_signals):
        return False, "Communication strategy is not meaningfully addressed."

    # 4. Risk + accountability acknowledgement
    risk_signals = [
        "risk",
        "impact",
        "exposure",
        "downside",
        "consequence",
        "accountability",
        "ownership",
        "follow-up",
    ]
    if not any(sig in full_text for sig in risk_signals):
        return False, "Risks and accountability are not acknowledged."

    return True, "Incident command governance decision demonstrates master-level judgment."
