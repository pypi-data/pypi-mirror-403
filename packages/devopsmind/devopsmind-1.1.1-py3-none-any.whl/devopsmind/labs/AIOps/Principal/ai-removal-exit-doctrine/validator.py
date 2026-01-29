import os
import re
import sys

REQUIRED_SECTIONS = [
    "Conditions Requiring Permanent AI Removal",
    "Rationale for Irreversible Exit",
    "Accountability for Delayed or Denied Removal",
    "Organizational AI Exit Doctrine",
    "Doctrine Defensibility",
]

ABSOLUTE_MARKERS = [
    "permanent",
    "irreversible",
    "never",
    "must not",
    "unacceptable",
    "non-negotiable",
]

LEGITIMACY_MARKERS = [
    "legitimacy",
    "illegitimate",
    "invalid",
    "no longer acceptable",
]

DELAY_ACCOUNTABILITY_MARKERS = [
    "delay",
    "postponed",
    "denied",
    "chose not to",
    "continued operation",
    "leadership responsibility",
]

PUBLIC_DEFENSE_MARKERS = [
    "board",
    "regulatory",
    "public",
    "legal",
    "scrutiny",
    "defensible",
]

FORBIDDEN_PHRASES = [
    "mitigate",
    "recover",
    "remediate",
    "rollback",
    "monitor",
    "control",
    "process",
    "workflow",
    "tooling",
    "framework",
]

def extract_section(content, section):
    pattern = rf"(?:^|\n)#\s+{re.escape(section)}\s*\n(.+?)(?=\n#\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""

def validate():
    filename = "ai_removal_exit_review.md"

    if not os.path.exists(filename):
        return False, (
            "ai_removal_exit_review.md is missing. "
            "A written AI removal and exit doctrine is required."
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
                "All exit doctrine components must be explicitly defined."
            )

    # 2. Irreversible exit language
    if not any(m in lowered for m in ABSOLUTE_MARKERS):
        return False, (
            "Exit doctrine lacks irreversible, non-negotiable positions. "
            "Principal-level exit doctrine must declare permanency."
        )

    # 3. Legitimacy invalidation
    if not any(m in lowered for m in LEGITIMACY_MARKERS):
        return False, (
            "Doctrine does not clearly articulate when AI legitimacy is lost."
        )

    # 4. Accountability for delay
    if not any(m in lowered for m in DELAY_ACCOUNTABILITY_MARKERS):
        return False, (
            "Accountability for delayed or denied removal is insufficiently addressed."
        )

    # 5. Public defensibility
    if not any(m in lowered for m in PUBLIC_DEFENSE_MARKERS):
        return False, (
            "Exit doctrine defensibility under board, regulatory, or public scrutiny "
            "is insufficiently addressed."
        )

    # 6. Reject operational framing
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            return False, (
                "Operational, recovery, or mitigation language detected. "
                "Exit doctrine defines limits, not execution."
            )

    return True, (
        "AI removal and exit doctrine defined successfully. "
        "The submission reflects Principal-level irreversible governance judgment."
    )

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
