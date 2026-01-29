import os
import re

def normalize_header(line):
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    """
    A section is considered incomplete only if:
    - It is empty, OR
    - It still contains instructional placeholder sentences
    """
    placeholder_phrases = [
        "identify which service failed first",
        "describe the initial problem",
        "explain how the failure",
        "dependency relationships",
        "explain why the initial failure",
    ]

    cleaned = text.strip().lower()

    if not cleaned:
        return True

    return any(phrase in cleaned for phrase in placeholder_phrases)

def validate():
    if not os.path.exists("analysis.txt"):
        return False, "analysis.txt not found."

    content = open("analysis.txt").read().lower()
    lines = content.splitlines()

    required_sections = [
        "initial failure",
        "failure propagation",
        "true root cause",
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

    # Ensure sections are not placeholders
    for section, lines in parts.items():
        text = " ".join(lines)
        if is_placeholder(text):
            return False, f"Section '{section.title()}' has not been completed."

    full_text = " ".join(" ".join(v) for v in parts.values())

    # Must identify an initial failing component
    if not any(
        phrase in full_text
        for phrase in ["failed first", "initial failure", "originated", "first occurred"]
    ):
        return False, "Initial failure is not clearly identified."

    # Must explain propagation through dependencies
    if not any(
        word in full_text
        for word in ["dependency", "dependent", "cascade", "propagate", "downstream"]
    ):
        return False, "Failure propagation through dependencies is not explained."

    # Must distinguish root cause from symptoms
    if not any(
        phrase in full_text
        for phrase in [
            "true root cause",
            "underlying cause",
            "not the root cause",
            "symptom",
            "originating cause",
        ]
    ):
        return False, "True root cause is not distinguished from downstream symptoms."

    return True, "Multi-service outage analyzed with expert-level causal reasoning."
