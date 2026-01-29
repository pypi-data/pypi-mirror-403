import os
import re

def normalize_header(line):
    """Normalize markdown headers like '## Trust Assessment' → 'trust assessment'"""
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    """Detect unchanged guidance or empty sections."""
    guidance_phrases = [
        "summarize metrics, logs, and alerts",
        "describe where signals disagree",
        "state which signals are more reliable",
        "explain how signal trust affects incident handling",
        "describe risks of trusting the wrong signals",
    ]
    return len(text.strip()) == 0 or any(p in text for p in guidance_phrases)

def has_substance(text, min_words=8):
    """Ensure section contains real reasoning."""
    return len(text.split()) >= min_words

def validate():
    if not os.path.exists("signal-trust-assessment.md"):
        return False, "signal-trust-assessment.md not found."

    content = open("signal-trust-assessment.md").read().lower()
    lines = content.splitlines()

    required_sections = [
        "signal overview",
        "conflicts and inconsistencies",
        "trust assessment",
        "decision impact",
        "risks and mitigations",
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

    # --- Expert intent checks (semantic, not keyword-tight) ---

    # 1. Must evaluate more than one type of signal
    signal_indicators = [
        "metric",
        "log",
        "alert",
        "signal",
        "telemetry",
        "data",
    ]
    if sum(1 for s in signal_indicators if s in full_text) < 2:
        return False, "Multiple observability signals are not evaluated."

    # 2. Must express relative confidence / reliability
    trust_signals = [
        "reliable",
        "less reliable",
        "more reliable",
        "confidence",
        "trust",
        "weight",
        "lean on",
        "prefer",
    ]
    if not any(sig in full_text for sig in trust_signals):
        return False, "Relative trust or confidence between signals is not explained."

    # 3. Must explain why one signal is trusted over another
    reasoning_signals = [
        "because",
        "due to",
        "based on",
        "indicates",
        "suggests",
        "aligns with",
        "contradicts",
    ]
    if not any(sig in full_text for sig in reasoning_signals):
        return False, "Signal trust decision is not justified with reasoning."

    # 4. Must acknowledge risk of incorrect trust
    risk_signals = [
        "risk",
        "misleading",
        "false",
        "blind spot",
        "incorrect",
        "miss",
        "delay",
        "wrong decision",
    ]
    if not any(sig in full_text for sig in risk_signals):
        return False, "Risks of trusting the wrong signals are not acknowledged."

    return True, "Observability signal trust assessed with expert-level judgment."
