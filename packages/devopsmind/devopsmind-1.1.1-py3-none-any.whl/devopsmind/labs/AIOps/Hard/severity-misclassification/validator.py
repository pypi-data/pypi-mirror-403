import os
import re


REQUIRED_SECTIONS = [
    "Incident Overview",
    "AI Severity Classification Impact",
    "Human Judgment Boundary",
    "Operational and Business Impact",
    "Accountability Assessment",
    "Post-Incident Decision",
]


def extract_section(content, section):
    pattern = rf"(?:^|\n)#\s+{re.escape(section)}\s*(.+?)(?=\n#\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""


def sentence_count(text, min_sentences=3):
    sentences = re.split(r"[.!?]", text)
    meaningful = [s for s in sentences if len(s.strip()) > 25]
    return len(meaningful) >= min_sentences


def contains_any(text, terms):
    return any(t in text for t in terms)


def validate(submission=None):
    if submission:
        content = submission
    else:
        if not os.path.exists("incident_assessment.md"):
            return False, "An incident analysis is required."
        with open("incident_assessment.md", encoding="utf-8") as f:
            content = f.read()

    lowered = content.lower()

    # 1. Structure & depth
    for section in REQUIRED_SECTIONS:
        body = extract_section(content, section)
        if not body:
            return False, "The analysis does not cover the full incident lifecycle."
        if not sentence_count(body):
            return False, "One or more sections lack sustained reasoning."

    # 2. Explicit human decision
    if not contains_any(lowered, [
        "decided", "chose", "did not escalate", "did not override",
        "accepted the classification", "took no action"
    ]):
        return False, (
            "The analysis must describe a specific human decision or non-decision."
        )

    # 3. Override point
    if not contains_any(lowered, [
        "should have overridden", "override point", "at the moment",
        "when customer impact", "when errors increased"
    ]):
        return False, (
            "The analysis must identify when human authority should have overridden automation."
        )

    # 4. Causal chain
    if not contains_any(lowered, [
        "because", "as a result", "which caused", "leading to"
    ]):
        return False, (
            "The analysis must clearly connect a human decision to impact."
        )

    # 5. Operational or business impact
    if not contains_any(lowered, [
        "outage", "downtime", "customer impact", "sla", "revenue",
        "reputational", "financial"
    ]):
        return False, (
            "Concrete operational or business impact is missing."
        )

    # 6. Accountability with role
    if not contains_any(lowered, [
        "on-call", "incident commander", "engineer", "sre", "lead"
    ]):
        return False, (
            "Accountability must be assigned to a specific operational role."
        )

    # 7. Post-incident authority or control change
    if not contains_any(lowered, [
        "restrict", "disable", "suspend", "require human approval",
        "remove authority from automation"
    ]):
        return False, (
            "The post-incident decision must define a concrete change in authority or control."
        )

    # 8. Tooling deflection guard
    if contains_any(lowered, [
        "retrain", "fine-tune", "prompt", "improve the model",
        "add monitoring", "better alerts"
    ]):
        return False, (
            "The analysis must focus on judgment and accountability, not tooling changes."
        )

    return True, "Incident analysis demonstrates sound judgment and accountability."
