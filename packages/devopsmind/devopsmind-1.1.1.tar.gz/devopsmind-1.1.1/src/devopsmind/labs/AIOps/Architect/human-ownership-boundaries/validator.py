import os
import re
import sys

REQUIRED_SECTIONS = [
    "Human Ownership Domains Assessed",
    "AI-Disallowed Ownership Boundaries",
    "AI-Permitted Ownership Domains",
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
    "assign role",
    "raci",
    "process",
    "workflow",
    "tooling",
    "framework",
    "guardrail",
]

def extract_section(content, section):
    pattern = rf"(?:^|\n)#\s+{re.escape(section)}\s*\n(.+?)(?=\n#\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""

def validate():
    filename = "human_ownership_boundary_review.md"

    if not os.path.exists(filename):
        return False, (
            "human_ownership_boundary_review.md is missing. "
            "A written human ownership boundary definition is required."
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
                "Each section must be addressed at platform scope."
            )

    # 2. Explicit disallowed ownership zones
    if not any(m in lowered for m in DISALLOWED_MARKERS):
        return False, (
            "Explicit AI-disallowed ownership boundaries are missing. "
            "Architect-level governance requires permanent exclusion zones."
        )

    # 3. Support vs ownership distinction
    if not any(m in lowered for m in SUPPORT_MARKERS):
        return False, (
            "AI-permitted support domains are not clearly distinguished "
            "from ownership or accountability."
        )

    # 4. Governance defensibility
    if not any(t in lowered for t in ["executive", "legal", "regulatory", "audit", "defensible"]):
        return False, (
            "Governance defensibility is insufficiently addressed. "
            "Ownership boundaries must survive legal and regulatory scrutiny."
        )

    # 5. Reject procedural framing
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            return False, (
                "Procedural or role-design language detected. "
                "This lab evaluates boundary definition, not organizational design."
            )

    return True, (
        "Human ownership boundaries defined successfully. "
        "The analysis reflects Architect-level governance judgment."
    )

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
