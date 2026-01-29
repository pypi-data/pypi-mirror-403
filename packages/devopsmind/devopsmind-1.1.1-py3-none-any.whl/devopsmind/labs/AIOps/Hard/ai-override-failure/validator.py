import os
import re


REQUIRED_SECTIONS = [
    "Incident Overview",
    "AI vs Reality Conflict",
    "Override Hesitation Analysis",
    "Operational and Business Impact",
    "Accountability Assessment",
    "Post-Incident Decision",
]

HESITATION_TERMS = [
    "hesitat",
    "fear",
    "uncertain",
    "defer",
    "over-trust",
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
    "training",
    "policy change",
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
    if not os.path.exists("override_failure_assessment.md"):
        return False, (
            "override_failure_assessment.md is missing. "
            "A written incident analysis is required."
        )

    with open("override_failure_assessment.md", encoding="utf-8") as f:
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
            "The analysis must explain why the override failed."
        )

    # 3. Human hesitation analysis
    if not any(t in lowered for t in HESITATION_TERMS):
        return False, (
            "Override hesitation is not sufficiently examined. "
            "The analysis must explain why humans deferred to AI "
            "despite conflicting evidence."
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
            "Clear restriction or removal of unsafe AI influence is expected."
        )

    # 6. Reject tooling / retraining framing
    for term in FORBIDDEN_TERMS:
        if term in lowered:
            return False, (
                "Tooling or retraining-focused solutions detected. "
                "This lab evaluates judgment, authority, and responsibility."
            )

    return True, (
        "Override failure analysis demonstrates clear reasoning, "
        "accountability, and decisive operational judgment."
    )
