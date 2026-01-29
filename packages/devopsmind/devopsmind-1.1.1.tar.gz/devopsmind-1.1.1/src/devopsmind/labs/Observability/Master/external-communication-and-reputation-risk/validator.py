import os
import re

def normalize_header(line):
    """Normalize markdown headers like '## Message Scope and Tone' → 'message scope and tone'"""
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    """Detect unchanged guidance or empty sections."""
    guidance_phrases = [
        "summarize incident status and public visibility",
        "state whether external communication will occur",
        "define what will and will not be communicated",
        "describe executive and legal approval flow",
        "explain how trust and credibility are protected",
    ]
    return len(text.strip()) == 0 or any(p in text for p in guidance_phrases)

def has_substance(text, min_words=10):
    """Ensure section contains real master-level reasoning."""
    return len(text.split()) >= min_words

def validate():
    if not os.path.exists("external-communication.md"):
        return False, "external-communication.md not found."

    content = open("external-communication.md").read().lower()
    lines = content.splitlines()

    required_sections = [
        "current situation",
        "communication decision",
        "message scope and tone",
        "approval and alignment",
        "reputational risks and mitigations",
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

    # Ensure sections are completed and substantive
    for section, lines in parts.items():
        text = " ".join(lines)
        if is_placeholder(text):
            return False, f"Section '{section.title()}' has not been completed."
        if not has_substance(text):
            return False, f"Section '{section.title()}' lacks sufficient depth."

    full_text = " ".join(" ".join(v) for v in parts.values())

    # --- Master-level intent checks (VERY loose) ---

    # 1. External-facing communication awareness
    external_signals = [
        "external",
        "public",
        "customer",
        "user",
        "partner",
        "press",
        "statement",
    ]
    if not any(sig in full_text for sig in external_signals):
        return False, "External communication context is not clearly considered."

    # 2. Approval / alignment with authority structures
    alignment_signals = [
        "approve",
        "alignment",
        "review",
        "sign-off",
        "leadership",
        "executive",
        "legal",
        "comms",
    ]
    if not any(sig in full_text for sig in alignment_signals):
        return False, "Approval or organizational alignment is not addressed."

    # 3. Avoid speculative or definitive claims
    speculative_phrases = [
        "root cause is",
        "definitely caused by",
        "confirmed cause",
        "we know exactly",
    ]
    if any(p in full_text for p in speculative_phrases):
        return False, "Speculative or definitive claims detected in external communication."

    # 4. Reputation, trust, or credibility awareness
    reputation_signals = [
        "trust",
        "confidence",
        "reputation",
        "credibility",
        "perception",
        "public confidence",
        "brand",
    ]
    if not any(sig in full_text for sig in reputation_signals):
        return False, "Reputational impact or trust considerations are not acknowledged."

    return True, "External communication decision demonstrates master-level judgment."
