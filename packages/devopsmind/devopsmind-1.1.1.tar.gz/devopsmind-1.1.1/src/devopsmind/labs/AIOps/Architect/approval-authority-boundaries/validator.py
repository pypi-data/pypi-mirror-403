import os
import re
import sys

REQUIRED_SECTIONS = [
    "Approval and Authority Domains Assessed",
    "AI-Disallowed Approval and Authority Boundaries",
    "AI-Permitted Approval Support Domains",
    "Boundary Rationale",
    "Governance Defensibility",
]

DISALLOWED_MARKERS = [
    "never",
    "must not",
    "disallowed",
    "prohibited",
    "cannot approve",
]

SUPPORT_MARKERS = [
    "assist",
    "inform",
    "support",
    "recommend",
    "advise",
]

FORBIDDEN_PHRASES = [
    "approval workflow",
    "escalation",
    "controls",
    "guardrails",
    "monitoring",
    "framework",
    "tooling",
]

def extract_section(content, section):
    pattern = rf"(?:^|\n)#\s+{re.escape(section)}\s*\n(.+?)(?=\n#\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""

def validate():
    filename = "approval_authority_boundary_review.md"

    if not os.path.exists(filename):
        return False, (
            "approval_authority_boundary_review.md is missing. "
            "A written authority boundary definition is required."
        )

    with open(filename, encoding="utf-8") as f:
        content = f.read()

    lowered = content.lower()

    # 1. Section presence
    for section in REQUIRED_SECTIONS:
        body = extract_section(content, section)
        if not body:
            return False, (
                f"The section '{section}' is missing or empty. "
                "Each section must be addressed at platform scope."
            )

    # 2. Explicit disallowed authority
    if not any(m in lowered for m in DISALLOWED_MARKERS):
        return False, (
            "Explicit AI-disallowed approval boundaries are missing. "
            "Architect-level governance requires permanent exclusion zones."
        )

    # 3. Support vs authority distinction
    if not any(m in lowered for m in SUPPORT_MARKERS):
        return False, (
            "AI-permitted support domains are not clearly distinguished "
            "from approval authority."
        )

    # 4. Governance defensibility
    if not any(t in lowered for t in ["legal", "regulatory", "audit", "executive", "defensible"]):
        return False, (
            "Governance defensibility is insufficiently addressed. "
            "Boundaries must survive legal and regulatory scrutiny."
        )

    # 5. Reject procedural framing
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            return False, (
                "Procedural or enforcement-focused language detected. "
                "This lab evaluates boundary definition, not implementation."
            )

    return True, (
        "Approval and authority boundaries defined successfully. "
        "The analysis reflects Architect-level platform governance judgment."
    )

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
