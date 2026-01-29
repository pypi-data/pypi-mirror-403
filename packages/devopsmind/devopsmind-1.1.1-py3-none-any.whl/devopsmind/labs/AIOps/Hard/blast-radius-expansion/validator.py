import os
import re


REQUIRED_SECTIONS = [
    "Incident and Initial Scope",
    "AI Influence on Scope Expansion",
    "Containment Breakdown",
    "Operational and Business Impact",
    "Accountability Assessment",
    "Post-Incident Decision",
]

BLAST_RADIUS_TERMS = [
    "blast radius",
    "scope expanded",
    "expanded impact",
    "spread",
    "propagated",
    "containment boundary",
]

CONTAINMENT_FAILURE_TERMS = [
    "containment failed",
    "boundary violated",
    "isolation broken",
    "segmentation failed",
    "controls bypassed",
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
    "rollback automation",
    "deployment fix",
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
    if not os.path.exists("blast_radius_assessment.md"):
        return False, (
            "blast_radius_assessment.md is missing. "
            "A written incident analysis is required."
        )

    with open("blast_radius_assessment.md", encoding="utf-8") as f:
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
            "The analysis must explain why the blast radius expanded."
        )

    # 3. Blast radius recognition
    if not any(t in lowered for t in BLAST_RADIUS_TERMS):
        return False, (
            "Blast radius expansion is not sufficiently examined. "
            "The analysis must explicitly address scope growth and propagation."
        )

    # 4. Containment breakdown
    if not any(t in lowered for t in CONTAINMENT_FAILURE_TERMS):
        return False, (
            "Containment failure is insufficiently analyzed. "
            "The analysis must identify where isolation or boundaries broke down."
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

    # 7. Reject tooling or automation deflection
    for term in FORBIDDEN_TERMS:
        if term in lowered:
            return False, (
                "Tooling or automation-focused solutions detected. "
                "This lab evaluates judgment, containment discipline, and accountability."
            )

    return True, (
        "Blast radius expansion analysis demonstrates clear reasoning, "
        "containment awareness, accountability, and decisive judgment."
    )
