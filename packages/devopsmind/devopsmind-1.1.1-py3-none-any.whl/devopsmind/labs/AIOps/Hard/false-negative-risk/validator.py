import os
import re


REQUIRED_SECTIONS = [
    "Incident Overview",
    "AI Non-Detection Impact",
    "Human Judgment Gap",
    "Operational and Business Impact",
    "Accountability Assessment",
    "Post-Incident Decision",
]

FALSE_NEGATIVE_TERMS = [
    "false negative",
    "not detected",
    "missed",
    "no alert",
    "silent failure",
    "absence of signal",
]

HUMAN_RELIANCE_TERMS = [
    "assumed",
    "trusted the ai",
    "over-trust",
    "defer",
    "hesitat",
    "authority",
    "relied on detection",
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
    "restrict",
    "disable",
    "suspend",
    "remove",
    "limit",
]

FORBIDDEN_TERMS = [
    "retrain",
    "prompt",
    "api",
    "improve detection",
    "add alerts",
    "monitoring",
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
    if not os.path.exists("false_negative_assessment.md"):
        return False, (
            "false_negative_assessment.md is missing. "
            "A written incident analysis is required."
        )

    with open("false_negative_assessment.md", encoding="utf-8") as f:
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
                "Surface-level descriptions are insufficient."
            )

    # 2. Causal reasoning
    if not any(m in lowered for m in CAUSAL_MARKERS):
        return False, (
            "Causal reasoning is missing. "
            "The analysis must explain why the false negative persisted."
        )

    # 3. False-negative recognition
    if not any(t in lowered for t in FALSE_NEGATIVE_TERMS):
        return False, (
            "False-negative behavior is not sufficiently examined. "
            "The analysis must explicitly address non-detection or absence of signals."
        )

    # 4. Human judgment gap
    if not any(t in lowered for t in HUMAN_RELIANCE_TERMS):
        return False, (
            "Human judgment gap is insufficiently analyzed. "
            "The analysis must explain how reliance on AI detection delayed action."
        )

    # 5. Accountability
    if not any(t in lowered for t in ACCOUNTABILITY_TERMS):
        return False, (
            "Accountability is insufficiently addressed. "
            "Responsibility and authority must be explicitly owned."
        )

    # 6. Decisive post-incident action
    if not any(t in lowered for t in DECISIVE_ACTION_TERMS):
        return False, (
            "Post-incident decision lacks decisive action. "
            "Clear restriction or removal of unsafe AI influence is expected."
        )

    # 7. Reject optimization or tooling deflection
    for term in FORBIDDEN_TERMS:
        if term in lowered:
            return False, (
                "Optimization or tooling-focused solutions detected. "
                "This lab evaluates judgment, detection risk, and accountability."
            )

    return True, (
        "False-negative analysis demonstrates clear reasoning, "
        "accountability, and decisive operational judgment."
    )
