import os
import re


REQUIRED_SECTIONS = [
    "Incident and Failure Overview",
    "Pre-Incident Trust Basis",
    "Trust Reassessment",
    "Ongoing Risk Exposure",
    "Accountability Assessment",
    "Post-Incident Decision",
]

TRUST_BASIS_TERMS = [
    "trusted",
    "confidence",
    "assumed reliability",
    "historical performance",
    "past success",
]

TRUST_REASSESSMENT_TERMS = [
    "no longer trust",
    "trust revoked",
    "trust reduced",
    "trust is not defensible",
    "cannot justify trust",
]

RISK_EXPOSURE_TERMS = [
    "ongoing risk",
    "continued exposure",
    "residual risk",
    "production risk",
    "future incidents",
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
    "revoke",
]

FORBIDDEN_TERMS = [
    "retrain",
    "prompt",
    "api",
    "rebuild trust",
    "monitor",
    "metrics",
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
    if not os.path.exists("post_incident_trust_assessment.md"):
        return False, (
            "post_incident_trust_assessment.md is missing. "
            "A written incident analysis is required."
        )

    with open("post_incident_trust_assessment.md", encoding="utf-8") as f:
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
                "Surface-level trust statements are insufficient."
            )

    # 2. Causal reasoning
    if not any(m in lowered for m in CAUSAL_MARKERS):
        return False, (
            "Causal reasoning is missing. "
            "The analysis must explain why trust must be reassessed."
        )

    # 3. Pre-incident trust basis
    if not any(t in lowered for t in TRUST_BASIS_TERMS):
        return False, (
            "Pre-incident trust basis is not sufficiently examined. "
            "The analysis must explain why the system was trusted before failure."
        )

    # 4. Trust reassessment
    if not any(t in lowered for t in TRUST_REASSESSMENT_TERMS):
        return False, (
            "Trust reassessment is insufficiently analyzed. "
            "The analysis must clearly state whether continued trust is defensible."
        )

    # 5. Ongoing risk exposure
    if not any(t in lowered for t in RISK_EXPOSURE_TERMS):
        return False, (
            "Ongoing risk exposure is not sufficiently addressed. "
            "The analysis must explain the risk of continued AI use."
        )

    # 6. Accountability
    if not any(t in lowered for t in ACCOUNTABILITY_TERMS):
        return False, (
            "Accountability is insufficiently addressed. "
            "Responsibility for trust decisions must be explicitly owned."
        )

    # 7. Decisive post-incident action
    if not any(t in lowered for t in DECISIVE_ACTION_TERMS):
        return False, (
            "Post-incident decision lacks decisive action. "
            "Clear restriction or revocation of unsafe trust is expected."
        )

    # 8. Reject trust-repair or tooling deflection
    for term in FORBIDDEN_TERMS:
        if term in lowered:
            return False, (
                "Trust-repair or tooling-focused language detected. "
                "This lab evaluates judgment and governance, not confidence rebuilding."
            )

    return True, (
        "Post-incident trust analysis demonstrates clear reasoning, "
        "explicit accountability, and appropriate governance judgment."
    )
