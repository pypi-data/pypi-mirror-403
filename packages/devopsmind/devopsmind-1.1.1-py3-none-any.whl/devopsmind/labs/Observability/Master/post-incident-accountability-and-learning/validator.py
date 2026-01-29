import os
import re

def normalize_header(line):
    """Normalize markdown headers like '## Organizational Learning' → 'organizational learning'"""
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    """Detect unchanged guidance or empty sections."""
    guidance_phrases = [
        "summarize what happened and why it matters",
        "explain how responsibility is addressed",
        "describe what the organization must learn",
        "identify decisions that permanently change",
        "explain how these decisions affect long-term trust",
    ]
    return len(text.strip()) == 0 or any(p in text for p in guidance_phrases)

def has_substance(text, min_words=10):
    """Ensure section contains real master-level reasoning."""
    return len(text.split()) >= min_words

def validate():
    if not os.path.exists("accountability-decision.md"):
        return False, "accountability-decision.md not found."

    content = open("accountability-decision.md").read().lower()
    lines = content.splitlines()

    required_sections = [
        "incident reflection",
        "accountability assessment",
        "organizational learning",
        "irreversible decisions",
        "trust and culture impact",
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

    # --- Master-level intent checks (VERY loose, culture-driven) ---

    # 1. Accountability without blame (fair responsibility framing)
    accountability_signals = [
        "accountability",
        "responsibility",
        "ownership",
        "role",
        "systemic",
        "process",
    ]
    if not any(sig in full_text for sig in accountability_signals):
        return False, "Accountability is not meaningfully addressed."

    # Avoid punitive framing without forcing exact words
    punitive_signals = [
        "punish",
        "punishment",
        "disciplinary",
        "terminate",
        "fire",
    ]
    if any(sig in full_text for sig in punitive_signals):
        return False, "Response focuses on punishment rather than accountability and learning."

    # 2. Organizational learning or change
    learning_signals = [
        "learn",
        "learning",
        "improve",
        "change",
        "evolve",
        "adjust",
        "strengthen",
    ]
    if not any(sig in full_text for sig in learning_signals):
        return False, "Organizational learning or change is not clearly articulated."

    # 3. Irreversible or long-term decisions
    irreversible_signals = [
        "permanent",
        "long-term",
        "irreversible",
        "structural",
        "fundamental",
        "cannot revert",
    ]
    if not any(sig in full_text for sig in irreversible_signals):
        return False, "Long-term or irreversible decisions are not clearly identified."

    # 4. Trust, culture, or psychological safety impact
    culture_signals = [
        "trust",
        "culture",
        "psychological safety",
        "confidence",
        "morale",
        "engagement",
        "ownership culture",
    ]
    if not any(sig in full_text for sig in culture_signals):
        return False, "Impact on trust, culture, or psychological safety is not acknowledged."

    return True, "Post-incident accountability and learning demonstrate master-level judgment."
