from pathlib import Path

TEMPLATE_MARKERS = [
    "describe what users experienced",
    "identify the first infrastructure component",
    "explain how the initial failure",
    "reconstruct the sequence of events"
]

def validate():
    rca_file = Path("rca.md")

    if not rca_file.exists():
        return False, "rca.md not found"

    text = rca_file.read_text().strip().lower()

    if len(text) < 400:
        return False, "RCA is too short for Hard-level analysis"

    # Template placeholder detection
    for marker in TEMPLATE_MARKERS:
        if marker in text:
            return False, "Template placeholders were not replaced"

    required_sections = [
        "observed impact",
        "initial failure",
        "failure propagation",
        "timeline correlation"
    ]

    for section in required_sections:
        if section not in text:
            return False, f"Missing required section: {section}"

    # Timeline awareness (HARD requirement)
    timeline_signals = [
        "16:",
        "timeline",
        "health probe",
        "traffic shifted",
        "latency"
    ]

    hits = sum(1 for signal in timeline_signals if signal in text)

    if hits < 3:
        return False, "RCA does not sufficiently reference the failure timeline"

    # Causal reasoning enforcement
    causal_terms = [
        "because",
        "led to",
        "resulted in",
        "therefore",
        "as a result"
    ]

    if not any(term in text for term in causal_terms):
        return False, "RCA lacks causal reasoning explaining outage propagation"

    return True, "Azure platform outage timeline successfully reconstructed"
