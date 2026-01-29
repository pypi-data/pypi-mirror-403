from pathlib import Path

TEMPLATE_MARKERS = [
    "describe which components",
    "explain how a request",
    "explain whether this exposure",
    "should not be directly accessible"
]

def validate():
    review = Path("architecture-review.md")

    if not review.exists():
        return False, "architecture-review.md not found"

    text = review.read_text().strip().lower()

    if len(text) < 200:
        return False, "Response is too short to demonstrate understanding"

    # ❌ Template placeholder detection
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
        "public",
        "private",
        "load balancer",
        "traffic"
    ]

    hits = sum(1 for word in reasoning_signals if word in text)

    if hits < 3:
        return False, "Response lacks basic architecture reasoning"

    return True, "Architecture exposure evaluation complete"
