import os
import re
import sys

REQUIRED_SECTIONS = [
    "Incident Response Phases Assessed",
    "AI-Disallowed Incident Response Boundaries",
    "AI-Permitted Incident Response Domains",
    "Boundary Rationale",
    "Governance Defensibility",
]

DISALLOWED_MARKERS = [
    "never",
    "must not",
    "disallowed",
    "prohibited",
    "cannot",
]

SUPPORT_MARKERS = [
    "assist",
    "support",
    "inform",
    "advise",
    "recommend",
]

FORBIDDEN_PHRASES = [
    "workflow",
    "process",
    "tooling",
    "framework",
    "guardrail",
    "approval flow",
]

def extract_section(content, section):
    pattern = rf"(?:^|\n)#\s+{re.escape(section)}\s*\n(.+?)(?=\n#\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""

def validate():
    filename = "incident_response_boundary_review.md"

    if not os.path.exists(filename):
        return False, (
            "incident_response_boundary_review.md is missing. "
            "A written incident response boundary definition is required."
        )

    with open(filename, encoding="utf-8") as f:
        content = f.read()

    lowered = content.lower()

    # 1. Required structure
    for section in REQUIRED_SECTIONS:
        body = extract_section(content, section)
        if not body:
            return False, (
                f"The section '{section}' is missing or empty. "
                "All incident response domains must be assessed."
            )

    # 2. Explicit disallowed incident domains
    if not any(m in lowered for m in DISALLOWED_MARKERS):
        return False, (
            "Explicit AI-disallowed incident response boundaries are missing. "
            "Architect-level governance requires permanent exclusion zones."
        )

    # 3. Support vs authority distinction
    if not any(m in lowered for m in SUPPORT_MARKERS):
        return False, (
            "AI-permitted support domains are not clearly separated "
            "from decision authority."
        )

    # 4. Accountability emphasis
    if not any(t in lowered for t in ["accountab", "ownership", "responsib"]):
        return False, (
            "Human accountability during incidents is insufficiently addressed."
        )

    # 5. Governance defensibility
    if not any(t in lowered for t in ["executive", "legal", "regulatory", "audit", "defensible"]):
        return False, (
            "Governance defensibility is insufficiently addressed. "
            "Incident response boundaries must survive post-incident scrutiny."
        )

    # 6. Reject procedural framing
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            return False, (
                "Procedural or operational framing detected. "
                "This lab evaluates boundary definition, not incident mechanics."
            )

    return True, (
        "Incident response boundaries defined successfully. "
        "The analysis reflects Architect-level governance judgment."
    )

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
