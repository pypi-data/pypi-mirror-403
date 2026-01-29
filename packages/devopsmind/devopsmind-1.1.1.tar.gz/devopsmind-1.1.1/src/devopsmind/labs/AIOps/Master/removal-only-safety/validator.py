import os
import re
import sys

REQUIRED_SECTIONS = [
    "Absence of Effective Safety Controls",
    "Exposure of Continued Operation",
    "Accountability Without Safeguards",
    "Removal Decision",
    "Governance Defensibility",
]

DECISION_TERMS = [
    "remove",
    "retain",
]

LAST_RESORT_TERMS = [
    "only",
    "last",
    "no other",
    "no effective",
    "no remaining",
    "exhausted",
]

FORBIDDEN_PHRASES = [
    "add controls",
    "alternative safeguards",
    "fallback",
    "monitor going forward",
    "introduce oversight",
    "framework",
]

def extract_section(content, section):
    pattern = rf"(?:^|\n)#\s+{re.escape(section)}\s*\n(.+?)(?=\n#\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""

def validate():
    filename = "removal_only_safety_review.md"

    if not os.path.exists(filename):
        return False, (
            "removal_only_safety_review.md is missing. "
            "A written last-resort safety assessment is required."
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

    # 2. Last-resort framing
    if not any(term in lowered for term in LAST_RESORT_TERMS):
        return False, (
            "The analysis does not clearly establish that removal "
            "is the only remaining effective safety control."
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
            "The decision should be explained in terms of long-term scrutiny."
        )

    # 5. Forbidden alternative-control framing
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            return False, (
                "Alternative control or fallback language detected. "
                "This lab evaluates last-resort decision-making, not safety redesign."
            )

    return True, (
        "Removal-only safety assessment completed successfully. "
        "The analysis demonstrates clear reasoning and a defensible decision."
    )

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
