import os
import re
import sys

REQUIRED_SECTIONS = [
    "Non-Delegable Decision Categories",
    "Rationale for Non-Delegation",
    "Accountability Implications",
    "Organizational Doctrine Statement",
    "Doctrine Defensibility",
]

NON_DELEGATION_MARKERS = [
    "never",
    "must not",
    "non-delegable",
    "cannot be delegated",
    "prohibited",
]

LEGITIMACY_MARKERS = [
    "legitimacy",
    "illegitimate",
    "invalid",
    "authority",
]

ACCOUNTABILITY_MARKERS = [
    "accountable",
    "ownership",
    "responsibility",
    "human-owned",
]

PUBLIC_DEFENSE_MARKERS = [
    "board",
    "legal",
    "regulatory",
    "public",
    "scrutiny",
    "defensible",
]

FORBIDDEN_PHRASES = [
    "mitigate",
    "control",
    "monitor",
    "process",
    "workflow",
    "tooling",
    "framework",
    "guardrail",
    "best practice",
]

def extract_section(content, section):
    pattern = rf"(?:^|\n)#\s+{re.escape(section)}\s*\n(.+?)(?=\n#\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""

def validate():
    filename = "non_delegable_decisions_review.md"

    if not os.path.exists(filename):
        return False, (
            "non_delegable_decisions_review.md is missing. "
            "A written non-delegation doctrine is required."
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
                "All non-delegation doctrine components must be defined."
            )

    # 2. Explicit non-delegation
    if not any(m in lowered for m in NON_DELEGATION_MARKERS):
        return False, (
            "Doctrine lacks explicit, absolute non-delegation positions."
        )

    # 3. Legitimacy framing
    if not any(m in lowered for m in LEGITIMACY_MARKERS):
        return False, (
            "Doctrine does not frame delegation limits as a legitimacy issue."
        )

    # 4. Accountability preservation
    if not any(m in lowered for m in ACCOUNTABILITY_MARKERS):
        return False, (
            "Accountability implications of non-delegation are insufficiently addressed."
        )

    # 5. Public defensibility
    if not any(m in lowered for m in PUBLIC_DEFENSE_MARKERS):
        return False, (
            "Doctrine defensibility under board, legal, or public scrutiny "
            "is insufficiently addressed."
        )

    # 6. Reject operational framing
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            return False, (
                "Operational or procedural language detected. "
                "Non-delegation doctrine defines legitimacy, not execution."
            )

    return True, (
        "Non-delegable decisions doctrine defined successfully. "
        "The submission reflects Principal-level governance judgment."
    )

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
