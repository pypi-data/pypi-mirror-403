import os
import re
import sys

REQUIRED_SECTIONS = [
    "Accepted AI Risk Categories",
    "Rationale for Risk Acceptance",
    "Accountability for Accepted Risk",
    "Organizational Risk Acceptance Doctrine",
    "Doctrine Defensibility",
]

ACCEPTANCE_MARKERS = [
    "accept",
    "accepted",
    "knowingly",
    "intentionally",
    "willing to bear",
]

OWNERSHIP_MARKERS = [
    "accountable",
    "ownership",
    "responsibility",
    "owned by",
    "leadership responsibility",
]

IRREVERSIBILITY_MARKERS = [
    "permanent",
    "binding",
    "irreversible",
    "non-negotiable",
]

PUBLIC_DEFENSE_MARKERS = [
    "board",
    "regulatory",
    "legal",
    "public",
    "scrutiny",
    "defensible",
]

FORBIDDEN_PHRASES = [
    "mitigate",
    "reduce",
    "control",
    "monitor",
    "process",
    "workflow",
    "tooling",
    "framework",
    "guardrail",
]

def extract_section(content, section):
    pattern = rf"(?:^|\n)#\s+{re.escape(section)}\s*\n(.+?)(?=\n#\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""

def validate():
    filename = "ai_risk_acceptance_review.md"

    if not os.path.exists(filename):
        return False, (
            "ai_risk_acceptance_review.md is missing. "
            "A written AI risk acceptance doctrine is required."
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
                "All risk acceptance components must be explicitly defined."
            )

    # 2. Explicit acceptance
    if not any(m in lowered for m in ACCEPTANCE_MARKERS):
        return False, (
            "Doctrine does not clearly state which risks are knowingly accepted."
        )

    # 3. Ownership of consequences
    if not any(m in lowered for m in OWNERSHIP_MARKERS):
        return False, (
            "Accountability for accepted risk is insufficiently defined."
        )

    # 4. Irreversibility
    if not any(m in lowered for m in IRREVERSIBILITY_MARKERS):
        return False, (
            "Risk acceptance must be framed as binding and irreversible."
        )

    # 5. Public defensibility
    if not any(m in lowered for m in PUBLIC_DEFENSE_MARKERS):
        return False, (
            "Doctrine defensibility under board, regulatory, or public scrutiny "
            "is insufficiently addressed."
        )

    # 6. Reject mitigation framing
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            return False, (
                "Mitigation or control language detected. "
                "Risk acceptance defines ownership, not reduction."
            )

    return True, (
        "AI risk acceptance doctrine defined successfully. "
        "The submission reflects Principal-level governance judgment."
    )

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
