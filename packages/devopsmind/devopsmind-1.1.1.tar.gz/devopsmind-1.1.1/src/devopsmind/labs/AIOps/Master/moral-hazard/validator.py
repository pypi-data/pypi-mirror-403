import os
import re
import sys

REQUIRED_SECTIONS = [
    "Evidence of Moral Hazard",
    "Risk Amplification Assessment",
    "Accountability and Consequence Ownership",
    "Removal Decision",
    "Governance Defensibility",
]

DECISION_TERMS = [
    "remove",
    "retain",
]

MORAL_HAZARD_TERMS = [
    "moral hazard",
    "riskier",
    "risk taking",
    "behavior",
    "incentive",
    "assume",
    "offload",
]

FORBIDDEN_PHRASES = [
    "train users",
    "policy change",
    "guardrails",
    "add controls",
    "monitor going forward",
    "framework",
]

def extract_section(content, section):
    pattern = rf"(?:^|\n)#\s+{re.escape(section)}\s*\n(.+?)(?=\n#\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""

def validate():
    filename = "moral_hazard_review.md"

    if not os.path.exists(filename):
        return False, (
            "moral_hazard_review.md is missing. "
            "A written moral hazard assessment is required."
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

    # 2. Moral hazard focus
    if not any(term in lowered for term in MORAL_HAZARD_TERMS):
        return False, (
            "Moral hazard or behavior-driven risk is not clearly articulated. "
            "The analysis should explain how behavior changed after automation."
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

    # 5. Forbidden behavior-correction framing
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            return False, (
                "Behavior-correction or control mechanisms detected. "
                "This lab evaluates assessment and decision-making, not fixes."
            )

    return True, (
        "Moral hazard assessment completed successfully. "
        "The analysis demonstrates clear reasoning and a defensible decision."
    )

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
