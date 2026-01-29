import os
import re


REQUIRED_SECTIONS = [
    "Incident Overview",
    "AI Silence and Its Impact",
    "Human Judgment Gap",
    "Operational and Business Impact",
    "Accountability Assessment",
    "Post-Incident Decision",
]

SILENT_FAILURE_TERMS = [
    "silent failure",
    "no signal",
    "absence of alerts",
    "no warning",
    "silence was interpreted",
    "lack of indication",
]

HUMAN_DEFERENCE_TERMS = [
    "assumed normal",
    "trusted silence",
    "defer",
    "over-trust",
    "waited for ai",
    "authority",
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
    "add monitoring",
    "alerts",
    "fix the ai",
    "optimize",
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
    if not os.path.exists("silent_failure_assessment.md"):
        return False, (
            "silent_failure_assessment.md is missing. "
            "A written incident analysis is required."
        )

    with open("silent_failure_assessment.md", encoding="utf-8") as f:
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
                "Silent failures require explicit analytical depth."
            )

    # 2. Causal reasoning
    if not any(m in lowered for m in CAUSAL_MARKERS):
        return False, (
            "Causal reasoning is missing. "
            "The analysis must explain how silence led to delayed response and impact."
        )

    # 3. Silent failure recognition
    if not any(t in lowered for t in SILENT_FAILURE_TERMS):
        return False, (
            "Silent failure is not explicitly analyzed. "
            "The absence of signals must be treated as a failure mode."
        )

    # 4. Human judgment gap
    if not any(t in lowered for t in HUMAN_DEFERENCE_TERMS):
        return False, (
            "Human judgment gap is insufficiently examined. "
            "The analysis must explain why silence was trusted."
        )

    # 5. Accountability
    if not any(t in lowered for t in ACCOUNTABILITY_TERMS):
        return False, (
            "Accountability is insufficiently addressed. "
            "Ownership of delayed detection must be explicit."
        )

    # 6. Decisive post-incident control
    if not any(t in lowered for t in DECISIVE_ACTION_TERMS):
        return False, (
            "Post-incident decision lacks decisive action. "
            "Silent failures require clear restriction of unsafe AI reliance."
        )

    # 7. Reject optimization / tooling deflection
    for term in FORBIDDEN_TERMS:
        if term in lowered:
            return False, (
                "Optimization or monitoring solutions detected. "
                "This lab evaluates judgment and accountability, not system tuning."
            )

    return True, (
        "Silent failure analysis demonstrates clear reasoning, "
        "human judgment awareness, and decisive operational control."
    )
