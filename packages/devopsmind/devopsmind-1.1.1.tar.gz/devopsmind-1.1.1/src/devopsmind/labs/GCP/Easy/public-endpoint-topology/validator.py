from pathlib import Path

TEMPLATE_MARKERS = [
    "describe which components are reachable",
    "describe which components should not",
    "explain how a request moves",
    "explain whether this exposure"
]

def validate():
    review = Path("architecture-review.md")

    if not review.exists():
        return False, "architecture-review.md not found"

    text = review.read_text().strip().lower()

    if len(text) < 200:
        return False, "Response is too short to demonstrate understanding"

    # Template placeholder detection
    for marker in TEMPLATE_MARKERS:
        if marker in text:
            return False, "Template placeholders were not replaced"

    required_sections = [
        "publicly exposed components",
        "private components",
        "request flow",
        "exposure assessment"
    ]

    for section in required_sections:
        if section not in text:
            return False, f"Missing required section: {section}"

    reasoning_signals = [
        "internet",
        "load balancer",
        "compute",
        "storage",
        "traffic"
    ]

    hits = sum(1 for signal in reasoning_signals if signal in text)

    if hits < 3:
        return False, "Response lacks basic GCP architecture reasoning"

    return True, "GCP public endpoint topology review complete"
