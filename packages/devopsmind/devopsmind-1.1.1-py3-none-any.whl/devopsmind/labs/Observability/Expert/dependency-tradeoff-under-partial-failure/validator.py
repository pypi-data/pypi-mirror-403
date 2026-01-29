import os
import re

def normalize_header(line):
    """Normalize markdown headers like '## Decision Rationale' → 'decision rationale'"""
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    """Detect unchanged guidance or empty sections."""
    guidance_phrases = [
        "describe the partial failure",
        "affected services",
        "possible degradation or protection choices",
        "should be prioritized and why",
        "risks introduced by the chosen trade-offs",
    ]
    return len(text.strip()) == 0 or any(p in text for p in guidance_phrases)

def has_substance(text, min_words=8):
    """Ensure section contains real reasoning."""
    return len(text.split()) >= min_words

def validate():
    if not os.path.exists("tradeoff-analysis.md"):
        return False, "tradeoff-analysis.md not found."

    content = open("tradeoff-analysis.md").read().lower()
    lines = content.splitlines()

    required_sections = [
        "situation overview",
        "trade-off options",
        "decision rationale",
        "risks and consequences",
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

    # --- Expert intent checks (semantic, NOT tight) ---

    # Must acknowledge shared dependency or coupling
    dependency_signals = [
        "dependency",
        "shared",
        "common",
        "coupled",
        "relies on",
        "depends on",
    ]
    if not any(sig in full_text for sig in dependency_signals):
        return False, "Shared dependency or coupling is not clearly discussed."

    # Must consider more than one service / capability
    service_signals = [
        "service",
        "component",
        "feature",
        "path",
        "workflow",
        "capability",
    ]
    if sum(1 for sig in service_signals if sig in full_text) < 2:
        return False, "Trade-offs across multiple services or capabilities are not considered."

    # Must make an explicit trade-off decision
    decision_signals = [
        "prioritize",
        "focus on",
        "protect",
        "degrade",
        "limit",
        "reduce",
        "sacrifice",
        "accept reduced",
    ]
    if not any(sig in full_text for sig in decision_signals):
        return False, "An explicit trade-off decision is missing."

    # Must acknowledge downsides / risks
    risk_signals = [
        "risk",
        "impact",
        "consequence",
        "downside",
        "trade-off",
        "cost",
    ]
    if not any(sig in full_text for sig in risk_signals):
        return False, "Risks or consequences of the trade-off are not acknowledged."

    return True, "Dependency trade-offs under partial failure evaluated with expert judgment."
