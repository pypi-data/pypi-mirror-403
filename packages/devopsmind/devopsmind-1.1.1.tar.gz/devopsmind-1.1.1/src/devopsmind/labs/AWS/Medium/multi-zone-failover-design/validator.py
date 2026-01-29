from pathlib import Path

def validate():
    review = Path("architecture-review.md")

    if not review.exists():
        return False, "architecture-review.md not found"

    doc = review.read_text().lower()

    required_sections = [
        "intended",
        "observed",
        "failover",
        "assessment"
    ]

    for section in required_sections:
        if section not in doc:
            return False, f"Missing required section: {section}"

    # Evidence awareness
    evidence_signals = [
        "availability zone",
        "us-east-1a",
        "us-east-1b",
        "load balancer",
        "unhealthy",
        "continued"
    ]

    hits = sum(1 for word in evidence_signals if word in doc)

    if hits < 4:
        return False, "Response does not sufficiently reference failure evidence"

    if "why" not in doc and "because" not in doc:
        return False, "Explanation lacks causal reasoning"

    return True, "Multi-AZ failover assessment validated"
