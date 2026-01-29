import os
import re


REQUIRED_SECTIONS = [
    "Incident and Escalation Overview",
    "AI Influence on Escalation Decisions",
    "Human Judgment Suppression",
    "Operational and Business Impact",
    "Accountability Assessment",
    "Post-Incident Decision",
]

AUTOMATION_BIAS_TERMS = [
    "automation bias",
    "defer",
    "over-trust",
    "trusted the ai",
    "followed the ai",
    "hesitat",
    "authority",
]

ACCOUNTABILITY_TERMS = [
    "accountab",
    "responsib",
    "owned",
    "authority",
    "decision rested",
]

DECISIVE_ACTION_TERMS = [
    "restrict",
    "disable",
    "suspend",
    "remove",
    "limit",
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

FORBIDDEN_TERMS = [
    "retrain",
    "prompt",
    "api",
    "improve the ai",
    "add alerts",
    "better escalation rules",
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
    if not os.path.exists("automation_bias_assessment.md"):
        return False, (
            "automation_bias_assessment.md is missing. "
            "A written incident analysis is required."
        )

    with open("automation_bias_assessment.md", encoding="utf-8") as f:
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
                "Summaries or surface-level statements are insufficient."
            )

    # 2. Causal reasoning
    if not any(m in lowered for m in CAUSAL_MARKERS):
        return False, (
            "Causal reasoning is missing. "
            "The analysis must explain why escalation was delayed."
        )

    # 3. Automation bias recognition
    if not any(t in lowered for t in AUTOMATION_BIAS_TERMS):
        return False, (
            "Automation bias is not sufficiently examined. "
            "The analysis must address how AI influence suppressed human judgment."
        )

    # 4. Accountability
    if not any(t in lowered for t in ACCOUNTABILITY_TERMS):
        return False, (
            "Accountability is insufficiently addressed. "
            "Responsibility and authority must be explicitly owned."
        )

    # 5. Decisive post-incident action
    if not any(t in lowered for t in DECISIVE_ACTION_TERMS):
        return False, (
            "Post-incident decision lacks decisive action. "
            "Clear restriction or removal of AI influence is expected."
        )

    # 6. Reject tooling / optimization framing
    for term in FORBIDDEN_TERMS:
        if term in lowered:
            return False, (
                "Tooling or optimization-focused solutions detected. "
                "This lab evaluates judgment, authority, and accountability."
            )

    return True, (
        "Automation bias analysis demonstrates clear reasoning, "
        "accountability, and decisive operational judgment."
    )
