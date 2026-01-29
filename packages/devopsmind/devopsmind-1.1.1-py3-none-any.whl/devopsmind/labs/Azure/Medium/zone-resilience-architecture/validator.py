from pathlib import Path

TEMPLATE_MARKERS = [
    "describe which components became unavailable",
    "explain which components continued",
    "describe how user traffic",
    "explain whether zone-level resilience"
]

def validate():
    review = Path("resilience-review.md")

    if not review.exists():
        return False, "resilience-review.md not found"

    text = review.read_text().strip().lower()

    if len(text) < 250:
        return False, "Response is too short for Medium-level reasoning"

    # Template placeholder detection
    for marker in TEMPLATE_MARKERS:
        if marker in text:
            return False, "Template placeholders were not replaced"

    required_sections = [
        "observed failure",
        "continued operation",
        "traffic handling",
        "resilience assessment"
    ]

    for section in required_sections:
        if section not in text:
            return False, f"Missing required section: {section}"

    # Evidence awareness (Medium requirement)
    evidence_signals = [
        "availability zone",
        "zone",
        "load balancer",
        "traffic",
        "continued"
    ]

    hits = sum(1 for signal in evidence_signals if signal in text)

    if hits < 3:
        return False, "Response does not sufficiently reference failure evidence"

    return True, "Azure zone-level resilience successfully evaluated"
