import os
import re


REQUIRED_SECTIONS = [
    "Confidence Drift Overview",
    "Impact on Human Decision-Making",
    "Judgment Boundary Failure",
    "Operational and Business Impact",
    "Accountability Assessment",
    "Post-Incident Decision",
]

CONFIDENCE_DRIFT_TERMS = [
    "confidence drift",
    "overconfidence",
    "increasing confidence",
    "false certainty",
    "perceived certainty",
]

JUDGMENT_SUPPRESSION_TERMS = [
    "defer",
    "hesitat",
    "trusted the ai",
    "over-trust",
    "authority",
    "reluctant to override",
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
    "tune",
    "prompt",
    "api",
    "monitoring",
    "confidence calibration",
    "fix the ai",
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
    if not os.path.exists("confidence_drift_assessment.md"):
        return False, (
            "confidence_drift_assessment.md is missing. "
            "A written incident analysis is required."
        )

    with open("confidence_drift_assessment.md", encoding="utf-8") as f:
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
            "The analysis must explain how confidence drift led to poor decisions."
        )

    # 3. Confidence drift recognition
    if not any(t in lowered for t in CONFIDENCE_DRIFT_TERMS):
        return False, (
            "Confidence drift is not sufficiently examined. "
            "The analysis must explain how expressed certainty diverged from reality."
        )

    # 4. Judgment boundary failure
    if not any(t in lowered for t in JUDGMENT_SUPPRESSION_TERMS):
        return False, (
            "Judgment boundary failure is insufficiently analyzed. "
            "The analysis must show how human judgment was suppressed by perceived AI certainty."
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

    # 7. Reject AI tuning or monitoring deflection
    for term in FORBIDDEN_TERMS:
        if term in lowered:
            return False, (
                "AI tuning or monitoring-focused solutions detected. "
                "This lab evaluates judgment boundaries and accountability, not system optimization."
            )

    return True, (
        "Confidence drift analysis demonstrates clear reasoning, "
        "judgment boundary awareness, accountability, and decisive action."
    )
