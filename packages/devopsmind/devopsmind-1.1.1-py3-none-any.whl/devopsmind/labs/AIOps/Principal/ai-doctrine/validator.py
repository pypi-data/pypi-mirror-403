import os
import re
import sys

REQUIRED_SECTIONS = [
    "Non-Negotiable AI Prohibitions",
    "Mandatory Human Ownership",
    "Unacceptable Failure Conditions",
    "Organizational AI Stance",
    "Doctrine Defensibility",
]

ABSOLUTE_MARKERS = [
    "never",
    "will not",
    "must not",
    "unacceptable",
    "prohibited",
    "non-negotiable",
]

OWNERSHIP_MARKERS = [
    "human",
    "accountable",
    "ownership",
    "responsibility",
    "cannot be delegated",
]

PUBLIC_DEFENSE_MARKERS = [
    "board",
    "regulatory",
    "public",
    "legal",
    "reputational",
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
    filename = "ai_doctrine_review.md"

    if not os.path.exists(filename):
        return False, (
            "ai_doctrine_review.md is missing. "
            "A written organizational AI doctrine is required."
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
                "All doctrine sections must be explicitly defined."
            )

    # 2. Non-negotiable positions
    if not any(m in lowered for m in ABSOLUTE_MARKERS):
        return False, (
            "Doctrine lacks explicit non-negotiable positions. "
            "Principal-level doctrine must declare absolutes."
        )

    # 3. Human ownership requirement
    if not any(m in lowered for m in OWNERSHIP_MARKERS):
        return False, (
            "Mandatory human ownership is insufficiently defined. "
            "Responsibility must be non-transferable."
        )

    # 4. Public and board defensibility
    if not any(m in lowered for m in PUBLIC_DEFENSE_MARKERS):
        return False, (
            "Doctrine defensibility under public, board, or regulatory scrutiny "
            "is insufficiently addressed."
        )

    # 5. Reject operational framing
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            return False, (
                "Operational or procedural language detected. "
                "Doctrine defines belief, not execution."
            )

    return True, (
        "AI doctrine defined successfully. "
        "The submission reflects Principal-level governance judgment."
    )

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
