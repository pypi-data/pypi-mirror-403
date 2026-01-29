import os
import re
import sys

REQUIRED_SECTIONS = [
    "Incident Influence Assessment",
    "Blast Radius Evaluation",
    "Accountability for Amplified Impact",
    "Removal Decision",
    "Governance Defensibility",
]

DECISION_TERMS = [
    "remove",
    "retain",
]

AMPLIFICATION_TERMS = [
    "amplif",
    "blast radius",
    "spread",
    "propagat",
    "accelerat",
]

FORBIDDEN_PHRASES = [
    "mitigate the risk",
    "contain the impact",
    "rollback",
    "add controls",
    "monitor going forward",
    "process change",
]

def extract_section(content, section):
    pattern = rf"(?:^|\n)#\s+{re.escape(section)}\s*\n(.+?)(?=\n#\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""

def validate():
    filename = "incident_amplification_review.md"

    if not os.path.exists(filename):
        return False, (
            "incident_amplification_review.md is missing. "
            "A written incident amplification assessment is required."
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

    # 2. Amplification focus
    if not any(term in lowered for term in AMPLIFICATION_TERMS):
        return False, (
            "Incident amplification is not clearly articulated. "
            "The analysis should explain how automation increased impact."
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
            "The decision should be explained in terms of post-incident review."
        )

    # 5. Forbidden remediation framing
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            return False, (
                "Remediation or containment language detected. "
                "This lab evaluates assessment and decision-making, not fixes."
            )

    return True, (
        "Incident amplification assessment completed successfully. "
        "The analysis demonstrates clear reasoning and a defensible decision."
    )

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
