import os
import re
import sys

REQUIRED_SECTIONS = [
    "Unacceptable Failure Categories",
    "Rationale for Unacceptability",
    "Accountability After Unacceptable Failure",
    "Organizational Doctrine Statement",
    "Doctrine Defensibility",
]

UNACCEPTABILITY_MARKERS = [
    "never",
    "unacceptable",
    "cannot be tolerated",
    "impermissible",
    "illegitimate",
    "invalidated",
    "refuses",
]

LEGITIMACY_MARKERS = [
    "legitimacy",
    "authority",
    "invalid",
    "collapse",
]

ACCOUNTABILITY_MARKERS = [
    "accountable",
    "ownership",
    "responsibility",
]

PUBLIC_SCRUTINY_MARKERS = [
    "board",
    "regulatory",
    "legal",
    "public",
    "scrutiny",
    "defensible",
]

# Only forbid ACTION-ORIENTED recovery language
FORBIDDEN_PATTERNS = [
    r"\bmitigat(e|ion)\b",
    r"\brecover(y|ed|ing)?\b",
    r"\bremediat(e|ion)\b",
    r"\bmonitor(ing)?\b",
    r"\bimplement(ed|ation)?\b",
    r"\bfix(ed|es|ing)?\b",
    r"\bimprov(e|ement|ing)?\b",
    r"\brepair(ed|ing)?\b",
]

def extract_section(content, section):
    pattern = rf"(?:^|\n)#\s+{re.escape(section)}\s*\n(.+?)(?=\n#\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""

def validate():
    filename = "unacceptable_failure_review.md"

    if not os.path.exists(filename):
        return False, (
            "unacceptable_failure_review.md is missing. "
            "A written unacceptable-failure doctrine is required."
        )

    with open(filename, encoding="utf-8") as f:
        content = f.read()

    lowered = content.lower()

    # 1. Required structure
    for section in REQUIRED_SECTIONS:
        body = extract_section(content, section)
        if not body:
            return False, (
                f"The section '{section}' is missing or empty. "
                "All unacceptable-failure doctrine components must be defined."
            )

    # 2. Explicit unacceptability
    if not any(m in lowered for m in UNACCEPTABILITY_MARKERS):
        return False, (
            "Doctrine does not declare absolute unacceptable failure positions."
        )

    # 3. Legitimacy invalidation
    if not any(m in lowered for m in LEGITIMACY_MARKERS):
        return False, (
            "Doctrine does not frame unacceptable failure as a legitimacy boundary."
        )

    # 4. Accountability clarity
    if not any(m in lowered for m in ACCOUNTABILITY_MARKERS):
        return False, (
            "Accountability after unacceptable failure is insufficiently defined."
        )

    # 5. Public defensibility
    if not any(m in lowered for m in PUBLIC_SCRUTINY_MARKERS):
        return False, (
            "Doctrine defensibility under board, regulatory, or public scrutiny "
            "is insufficiently addressed."
        )

    # 6. Reject procedural recovery framing
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, lowered):
            return False, (
                "Recovery, mitigation, or procedural language detected. "
                "Unacceptable failure doctrine defines refusal, not response."
            )

    return True, (
        "Unacceptable failure doctrine defined successfully. "
        "The submission reflects Principal-level governance judgment."
    )

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
