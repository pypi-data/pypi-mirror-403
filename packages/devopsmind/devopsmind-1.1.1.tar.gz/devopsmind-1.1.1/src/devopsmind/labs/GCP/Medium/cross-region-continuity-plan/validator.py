from pathlib import Path

TEMPLATE_MARKERS = [
    "describe which infrastructure",
    "explain which components",
    "describe how user traffic",
    "explain whether service continuity"
]

def validate():
    review = Path("continuity-review.md")
    artifacts_dir = Path("artifacts")

    if not review.exists():
        return False, "continuity-review.md not found"

    if not artifacts_dir.exists():
        return False, "artifacts directory is missing"

    text = review.read_text().strip().lower()

    if len(text) < 250:
        return False, "Response is too short for Medium-level reasoning"

    for marker in TEMPLATE_MARKERS:
        if marker in text:
            return False, "Template placeholders were not replaced"

    required_sections = [
        "observed failure",
        "continuity behavior",
        "traffic handling",
        "continuity assessment"
    ]

    for section in required_sections:
        if section not in text:
            return False, f"Missing required section: {section}"

    evidence_signals = [
        "region",
        "load balancer",
        "traffic",
        "continued",
        "unavailable"
    ]

    hits = sum(1 for signal in evidence_signals if signal in text)

    if hits < 3:
        return False, "Response does not sufficiently reference failure evidence"

    return True, "GCP service continuity assessment validated"
