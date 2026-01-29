import os
import re

REQUIRED_SECTIONS = [
    "Accountability Breakdown Assessment",
    "Organizational Impact of Accountability Collapse",
    "Implicit Risk Ownership",
    "Removal Decision",
    "Governance Defensibility",
]

CAUSAL_MARKERS = [
    "because",
    "therefore",
    "as a result",
    "led to",
    "caused",
    "resulted in",
    "due to",
]

ACCOUNTABILITY_TERMS = [
    "accountab",
    "ownership",
    "owned",
    "authority",
    "responsibility",
    "decision rested",
]

DECISION_TERMS = [
    "remove",
    "retain",
]

# Governance-diluting phrases ONLY (no generic language)
FORBIDDEN_PHRASES = [
    "mitigate the risk",
    "risk mitigation",
    "monitor going forward",
    "improve the system",
    "fix the issue",
    "clarify responsibilities",
    "add ownership",
    "introduce controls",
    "add oversight",
    "process improvement",
    "governance framework",
    "future improvement",
    "phased approach",
    "conditional approval",
    "temporary approval",
    "revisit later",
]

def extract_section(content, section):
    pattern = rf"(?:^|\n)#\s+{re.escape(section)}\s*\n(.+?)(?=\n#\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""

def validate():
    filename = "accountability_collapse_review.md"

    if not os.path.exists(filename):
        return False, (
            "accountability_collapse_review.md is missing. "
            "A written governance decision is required."
        )

    with open(filename, encoding="utf-8") as f:
        content = f.read()

    lowered = content.lower()

    # 1. Required structure
    for section in REQUIRED_SECTIONS:
        body = extract_section(content, section)
        if not body:
            return False, (
                f"Section '{section}' is missing, incorrectly formatted, "
                "or empty. All sections must use a single '#' heading."
            )

    # 2. Causal reasoning (required)
    if not any(marker in lowered for marker in CAUSAL_MARKERS):
        return False, (
            "Causal reasoning is missing. "
            "Accountability collapse must be explained, not asserted."
        )

    # 3. Accountability ownership
    if not any(term in lowered for term in ACCOUNTABILITY_TERMS):
        return False, (
            "Accountability ownership is not explicitly addressed. "
            "Responsibility must be owned by a role or authority."
        )

    # 4. Decision enforcement (exactly one)
    decision_hits = sum(1 for d in DECISION_TERMS if d in lowered)
    if decision_hits != 1:
        return False, (
            "Exactly one irreversible decision is required: remove or retain."
        )

    # 5. Governance defensibility
    if not any(term in lowered for term in ["defensible", "audit", "executive", "review"]):
        return False, (
            "Governance defensibility under executive or audit review is missing."
        )

    # 6. Forbidden governance deflection (loose-keyed)
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            return False, (
                "Governance deflection detected. "
                "This lab evaluates judgment, not repair strategies."
            )

    return True, "PASS"
