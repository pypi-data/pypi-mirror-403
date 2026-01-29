import os
import re

def normalize_header(line):
    """Normalize markdown headers like '## Stakeholder Priorities' → 'stakeholder priorities'"""
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    """Detect unchanged guidance or empty sections."""
    guidance_phrases = [
        "summarize the incident and current impact",
        "describe engineering, business, and compliance concerns",
        "state the chosen course of action",
        "explain why this decision balances risk and impact",
        "describe risks introduced by this decision",
    ]
    return len(text.strip()) == 0 or any(p in text for p in guidance_phrases)

def has_substance(text, min_words=8):
    """Ensure section contains real reasoning."""
    return len(text.split()) >= min_words

def validate():
    if not os.path.exists("stakeholder-decision.md"):
        return False, "stakeholder-decision.md not found."

    content = open("stakeholder-decision.md").read().lower()
    lines = content.splitlines()

    required_sections = [
        "situation overview",
        "stakeholder priorities",
        "decision",
        "justification",
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

    # Ensure all required sections exist
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

    # 1. Must consider multiple stakeholder perspectives
    stakeholder_signals = [
        "engineering",
        "business",
        "product",
        "compliance",
        "legal",
        "security",
        "operations",
        "customer",
        "leadership",
    ]
    if sum(1 for sig in stakeholder_signals if sig in full_text) < 2:
        return False, "Multiple stakeholder perspectives are not clearly considered."

    # 2. Must make a clear decision
    decision_signals = [
        "we will",
        "we will not",
        "i will",
        "i will not",
        "decide",
        "choose",
        "proceed",
        "hold",
        "delay",
    ]
    if not any(sig in full_text for sig in decision_signals):
        return False, "A clear decision is not stated."

    # 3. Must explain trade-offs or balancing logic
    tradeoff_signals = [
        "balance",
        "trade-off",
        "compromise",
        "weigh",
        "at the cost of",
        "while accepting",
    ]
    if not any(sig in full_text for sig in tradeoff_signals):
        return False, "Trade-offs between stakeholder priorities are not explained."

    # 4. Must acknowledge risks or downsides
    risk_signals = [
        "risk",
        "impact",
        "downside",
        "consequence",
        "exposure",
        "mitigation",
    ]
    if not any(sig in full_text for sig in risk_signals):
        return False, "Risks and mitigations are not acknowledged."

    return True, "Stakeholder priority conflict resolved with expert-level judgment."
