import os
import re
import sys

REQUIRED_SECTIONS = [
    "Operational Trust Assessment",
    "Organizational Impact of Trust Loss",
    "Accountability and Risk Ownership",
    "Removal Decision",
    "Governance Defensibility",
]

DECISION_TERMS = [
    "remove",
    "retain",
]

TRUST_LOSS_TERMS = [
    "trust",
    "distrust",
    "bypass",
    "override",
    "workaround",
    "behavior",
    "confidence",
]

FORBIDDEN_PHRASES = [
    "rebuild trust",
    "restore trust",
    "improve accuracy",
    "monitor going forward",
    "add oversight",
    "introduce controls",
    "process change",
]

def extract_section(content, section):
    pattern = rf"(?:^|\n)#\s+{re.escape(section)}\s*\n(.+?)(?=\n#\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""

def validate():
    filename = "trust_loss_review.md"

    if not os.path.exists(filename):
        return False, (
            "trust_loss_review.md is missing. "
            "A written trust loss assessment is required."
        )

    with open(filename, encoding="utf-8") as f:
        content = f.read()

    lowered = content.lower()

    # 1. Section presence
    for section in REQUIRED_SECTIONS:
        body = extract_section(content, section)
        if not body:
            return False, (
                f"The section '{section}' is missing or empty. "
                "Each section should address the topic described in the template."
            )

    # 2. Trust loss focus
    if not any(term in lowered for term in TRUST_LOSS_TERMS):
        return False, (
            "Operational trust loss is not clearly articulated. "
            "The analysis should explain how human behavior changed due to distrust."
        )

    # 3. Decision clarity
    decision_hits = sum(1 for d in DECISION_TERMS if d in lowered)
    if decision_hits == 0:
        return False, (
            "A clear removal or retention decision is missing."
        )
    if decision_hits > 1:
        return False, (
            "Multiple conflicting decisions detected. "
            "The assessment should converge on a single outcome."
        )

    # 4. Governance defensibility
    if not any(term in lowered for term in ["defensible", "audit", "executive", "review"]):
        return False, (
            "Governance defensibility is not clearly addressed. "
            "The decision should be explained in terms of executive or audit scrutiny."
        )

    # 5. Forbidden trust-recovery framing
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            return False, (
                "Trust recovery or optimization language detected. "
                "This lab evaluates assessment and decision-making, not fixes."
            )

    return True, (
        "Trust loss assessment completed successfully. "
        "The analysis demonstrates clear reasoning and a defensible decision."
    )

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
