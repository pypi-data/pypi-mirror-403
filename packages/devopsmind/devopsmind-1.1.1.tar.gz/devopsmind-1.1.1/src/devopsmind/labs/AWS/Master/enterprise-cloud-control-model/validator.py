from pathlib import Path

TEMPLATE_MARKERS = [
    "define where this control model applies",
    "describe how cost, reliability, and security responsibility",
    "explain how cloud cost is governed",
    "describe high-level constraints that reduce risk",
    "explain the compromises this control model makes"
]

def validate():
    policy_file = Path("cloud-governance-policy.md")

    if not policy_file.exists():
        return False, "cloud-governance-policy.md not found"

    text = policy_file.read_text().strip().lower()

    if len(text) < 500:
        return False, "Policy is too short for Master-level judgment"

    # ❌ Template placeholder detection
    for marker in TEMPLATE_MARKERS:
        if marker in text:
            return False, "Template placeholders were not replaced"

    required_sections = [
        "scope",
        "ownership model",
        "cost control principles",
        "usage guardrails",
        "trade-off considerations"
    ]

    for section in required_sections:
        if section not in text:
            return False, f"Missing required section: {section}"

    # Evidence awareness (org + cost + constraints)
    evidence_signals = [
        "team",
        "organization",
        "cost",
        "ownership",
        "autonomy",
        "constraint"
    ]

    hits = sum(1 for signal in evidence_signals if signal in text)

    if hits < 5:
        return False, "Policy does not sufficiently reflect provided evidence"

    # Explicit trade-off reasoning (MASTER requirement)
    tradeoff_terms = [
        "trade-off",
        "balance",
        "however",
        "risk",
        "impact",
        "at the cost of"
    ]

    if not any(term in text for term in tradeoff_terms):
        return False, "Policy lacks explicit trade-off reasoning"

    return True, "Master-level cloud governance judgment validated"
