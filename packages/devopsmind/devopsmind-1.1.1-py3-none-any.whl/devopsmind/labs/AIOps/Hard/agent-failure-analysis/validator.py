import os
import re


REQUIRED_SECTIONS = [
    "Failure Description",
    "Impact",
    "Root Cause",
    "Containment",
    "Prevention"
]

FORBIDDEN_PHRASES = [
    "auto-remediate",
    "self-healing",
    "execute automatically",
    "no human review"
]

TEMPLATE_MARKERS = [
    "include:",
    "explain",
    "examples:",
    "describe",
    "consider:",
    "avoid blaming",
    "do not suggest"
]

CAUSAL_MARKERS = [
    "because",
    "therefore",
    "as a result",
    "led to",
    "caused",
    "resulted in",
    "due to"
]

ACCOUNTABILITY_TERMS = [
    "accountab",
    "responsib",
    "owned",
    "authority",
    "decision rested",
    "we failed",
    "the team failed"
]

DECISIVE_ACTION_TERMS = [
    "restrict",
    "disable",
    "suspend",
    "remove",
    "limit"
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
    if not os.path.exists("failure_analysis.md"):
        return False, (
            "failure_analysis.md is missing. "
            "A written incident analysis is required."
        )

    with open("failure_analysis.md", encoding="utf-8") as f:
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

    # 2. Remove instructional scaffolding
    for marker in TEMPLATE_MARKERS:
        if marker in lowered:
            return False, (
                "Instructional template language is still present. "
                "Replace all guidance with original incident analysis."
            )

    # 3. Unsafe autonomy assumptions
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            return False, (
                f"Unsafe autonomy assumption detected: '{phrase}'. "
                "Post-failure systems must retain human control."
            )

    # 4. Causal reasoning
    if not any(m in lowered for m in CAUSAL_MARKERS):
        return False, (
            "Causal reasoning is missing. "
            "The analysis must explain why the failure occurred."
        )

    # 5. Accountability
    if not any(t in lowered for t in ACCOUNTABILITY_TERMS):
        return False, (
            "Accountability is insufficiently addressed. "
            "Responsibility and authority must be explicitly owned."
        )

    # 6. Decisive prevention or control action
    if not any(t in lowered for t in DECISIVE_ACTION_TERMS):
        return False, (
            "Prevention section lacks decisive action. "
            "Clear restriction or limitation of unsafe behavior is expected."
        )

    return True, (
        "Failure analysis demonstrates clear reasoning, accountability, "
        "and appropriate safety-focused judgment."
    )
