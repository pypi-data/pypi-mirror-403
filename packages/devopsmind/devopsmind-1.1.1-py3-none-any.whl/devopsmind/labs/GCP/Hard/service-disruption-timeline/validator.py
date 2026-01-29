from pathlib import Path

TEMPLATE_MARKERS = [
    "describe what users experienced",
    "identify the first infrastructure component",
    "explain how the initial failure",
    "reconstruct the sequence of events"
]

def validate():
    rca_file = Path("rca.md")
    artifacts_dir = Path("artifacts")

    if not rca_file.exists():
        return False, "rca.md not found"

    if not artifacts_dir.exists():
        return False, "artifacts directory is missing"

    text = rca_file.read_text().strip().lower()

    if len(text) < 400:
        return False, "RCA is too short for Hard-level analysis"

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

    timeline_signals = [
        "11:",
        "health",
        "traffic",
        "latency",
        "timeline"
    ]

    hits = sum(1 for signal in timeline_signals if signal in text)

    if hits < 3:
        return False, "RCA does not sufficiently reference the failure timeline"

    causal_terms = [
        "because",
        "led to",
        "resulted in",
        "therefore",
        "as a result"
    ]

    if not any(term in text for term in causal_terms):
        return False, "RCA lacks causal reasoning explaining failure propagation"

    return True, "Service disruption timeline successfully reconstructed"
