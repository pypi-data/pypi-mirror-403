import os
import re


REQUIRED_SECTIONS = [
    "Incident Timeline Overview",
    "AI-Induced Latency",
    "Human Decision Suppression",
    "Operational and Business Impact",
    "Accountability Assessment",
    "Post-Incident Decision",
]

LATENCY_TERMS = [
    "delay",
    "latency",
    "waited",
    "waiting",
    "paused",
    "slow",
    "time-critical",
    "response time",
]

HUMAN_SUPPRESSION_TERMS = [
    "defer",
    "hesitat",
    "awaited",
    "reluctant",
    "authority",
    "trusted the ai",
    "over-trust",
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
    "remove",
    "suspend",
    "limit",
]

FORBIDDEN_TERMS = [
    "optimize",
    "retrain",
    "prompt",
    "api",
    "parallelize",
    "faster model",
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
    if not os.path.exists("decision_latency_assessment.md"):
        return False, (
            "decision_latency_assessment.md is missing. "
            "A written incident analysis is required."
        )

    with open("decision_latency_assessment.md", encoding="utf-8") as f:
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
            "The analysis must explain why decision latency occurred."
        )

    # 3. Latency recognition
    if not any(t in lowered for t in LATENCY_TERMS):
        return False, (
            "Decision latency is not sufficiently examined. "
            "The analysis must explicitly address delays in human action."
        )

    # 4. Human decision suppression
    if not any(t in lowered for t in HUMAN_SUPPRESSION_TERMS):
        return False, (
            "Human decision suppression is insufficiently analyzed. "
            "The analysis must show how AI involvement delayed human action."
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

    # 7. Reject optimization / redesign deflection
    for term in FORBIDDEN_TERMS:
        if term in lowered:
            return False, (
                "Optimization or redesign-focused solutions detected. "
                "This lab evaluates judgment, time-critical risk, and accountability."
            )

    return True, (
        "Decision latency analysis demonstrates clear reasoning, "
        "accountability, and appropriate control decisions."
    )
