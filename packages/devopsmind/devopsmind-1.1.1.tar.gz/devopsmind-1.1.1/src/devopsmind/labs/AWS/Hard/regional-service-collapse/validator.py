from pathlib import Path

TEMPLATE_MARKERS = [
    "describe what users experienced",
    "explain the main architectural reason",
    "list architectural or capacity-related factors",
    "explain why a localized failure"
]

def validate():
    rca_file = Path("rca.md")

    if not rca_file.exists():
        return False, "rca.md not found"

    text = rca_file.read_text().strip().lower()

    if len(text) < 400:
        return False, "RCA is too short for a Hard-level analysis"

    # Template placeholder detection
    for marker in TEMPLATE_MARKERS:
        if marker in text:
            return False, "Template placeholders were not replaced"

    required_sections = [
        "observed failure",
        "primary architectural cause",
        "contributing factors",
        "failure propagation"
    ]

    for section in required_sections:
        if section not in text:
            return False, f"Missing required section: {section}"

    # Evidence correlation
    evidence_signals = [
        "us-east-1a",
        "us-east-1b",
        "latency",
        "overloaded",
        "traffic shifted",
        "health check",
        "unhealthy",
        "region"
    ]

    hits = sum(1 for signal in evidence_signals if signal in text)

    if hits < 4:
        return False, "RCA does not sufficiently explain regional service impact"

    causal_terms = [
        "because",
        "led to",
        "resulted in",
        "therefore",
        "as a result"
    ]

    if not any(term in text for term in causal_terms):
        return False, "RCA lacks causal reasoning explaining failure propagation"

    return True, "Regional service collapse RCA validated"
