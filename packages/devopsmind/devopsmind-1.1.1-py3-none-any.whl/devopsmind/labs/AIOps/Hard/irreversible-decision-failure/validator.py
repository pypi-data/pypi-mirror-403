import os
import re


REQUIRED_SECTIONS = [
    "Decision Overview",
    "AI Influence on the Decision",
    "Irreversibility Boundary Failure",
    "Permanent Impact Assessment",
    "Accountability Assessment",
    "Post-Incident Decision",
]

IRREVERSIBILITY_TERMS = [
    "irreversible",
    "irreversibility",
    "permanent",
    "cannot be undone",
    "no rollback",
    "one-way",
]

BOUNDARY_FAILURE_TERMS = [
    "boundary failed",
    "safeguard failed",
    "control bypassed",
    "authority violated",
    "should not have allowed",
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
    "responsib",
    "owned",
    "authority",
    "decision rested",
    "we failed",
    "the team failed",
]

DECISIVE_ACTION_TERMS = [
    "permanently disable",
    "permanently remove",
    "prohibit",
    "ban",
    "never allow",
]

FORBIDDEN_TERMS = [
    "rollback",
    "recover",
    "retrain",
    "prompt",
    "api",
    "mitigation plan",
    "fix",
]


def extract_section(content, section):
    """
    Accepts ONLY single '#' headings, exactly matching the template.
    """
    pattern = rf"(?:^|\n)#\s+{re.escape(section)}\s*\n(.+?)(?=\n#\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""


def section_substantive(text, min_sentences=3):
    sentences = re.split(r"[.!?]", text)
    meaningful = [s for s in sentences if len(s.strip()) > 20]
    return len(meaningful) >= min_sentences


def validate():
    if not os.path.exists("irreversible_decision_assessment.md"):
        return False, (
            "irreversible_decision_assessment.md is missing. "
            "A written incident analysis is required."
        )

    with open("irreversible_decision_assessment.md", encoding="utf-8") as f:
        content = f.read()

    lowered = content.lower()

    # 1. Structure + substance
    for section in REQUIRED_SECTIONS:
        body = extract_section(content, section)
        if not body:
            return False, (
                f"Section '{section}' is missing, incorrectly formatted, "
                "or empty. All sections must use a single '#' heading."
            )
        if not section_substantive(body):
            return False, (
                f"Section '{section}' lacks sustained reasoning. "
                "Surface-level statements are insufficient for irreversible decisions."
            )

    # 2. Causal reasoning
    if not any(m in lowered for m in CAUSAL_MARKERS):
        return False, (
            "Causal reasoning is missing. "
            "The analysis must explain why irreversibility safeguards failed."
        )

    # 3. Irreversibility recognition
    if not any(t in lowered for t in IRREVERSIBILITY_TERMS):
        return False, (
            "Irreversibility is not sufficiently examined. "
            "The analysis must explicitly address permanent or one-way impact."
        )

    # 4. Boundary failure
    if not any(t in lowered for t in BOUNDARY_FAILURE_TERMS):
        return False, (
            "Irreversibility boundary failure is insufficiently analyzed. "
            "The analysis must explain why AI involvement was allowed despite permanent risk."
        )

    # 5. Accountability
    if not any(t in lowered for t in ACCOUNTABILITY_TERMS):
        return False, (
            "Accountability is insufficiently addressed. "
            "Responsibility for the irreversible decision must be explicitly owned."
        )

    # 6. Permanent post-incident action
    if not any(t in lowered for t in DECISIVE_ACTION_TERMS):
        return False, (
            "Post-incident decision lacks firm, permanent action. "
            "Clear prohibition of unsafe AI involvement is expected."
        )

    # 7. Reject remediation or optimization framing
    for term in FORBIDDEN_TERMS:
        if term in lowered:
            return False, (
                "Remediation or optimization-focused language detected. "
                "This lab evaluates judgment after irreversible harm, not recovery tactics."
            )

    return True, (
        "Irreversible decision analysis demonstrates clear reasoning, "
        "explicit accountability, and firm governance judgment."
    )
