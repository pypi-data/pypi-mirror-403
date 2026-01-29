from pathlib import Path

TEMPLATE_MARKERS = [
    "describe the identity",
    "explain how access expanded",
    "identify which trust",
    "explain why the incident"
]

def validate():
    analysis_file = Path("security-analysis.md")

    if not analysis_file.exists():
        return False, "security-analysis.md not found"

    text = analysis_file.read_text().strip().lower()

    if len(text) < 350:
        return False, "Analysis is too short for Expert-level reasoning"

    # Template placeholder detection
    for marker in TEMPLATE_MARKERS:
        if marker in text:
            return False, "Template placeholders were not replaced"

    required_sections = [
        "security boundaries",
        "incident propagation",
        "boundary failures",
        "blast radius"
    ]

    for section in required_sections:
        if section not in text:
            return False, f"Missing required section: {section}"

    # Evidence correlation (Expert requirement)
    evidence_signals = [
        "managed identity",
        "shared",
        "lateral",
        "blob storage",
        "virtual machine",
        "virtual network",
        "resource group"
    ]

    hits = sum(1 for signal in evidence_signals if signal in text)

    if hits < 4:
        return False, "Analysis does not sufficiently reference incident evidence"

    # Causal reasoning enforcement
    causal_terms = [
        "because",
        "allowed",
        "resulted in",
        "led to",
        "therefore"
    ]

    if not any(term in text for term in causal_terms):
        return False, "Analysis lacks causal reasoning explaining blast radius"

    return True, "Expert-level Azure identity boundary failure analysis validated"
