import os
import re
import sys

REQUIRED_SECTIONS = [
    "Platform Domains Assessed",
    "AI-Disallowed Boundaries",
    "AI-Permitted Domains",
    "Boundary Rationale",
    "Governance Defensibility",
]

DISALLOWED_MARKERS = [
    "never",
    "must not",
    "disallowed",
    "prohibited",
    "cannot",
    "categorically",
]

PERMISSION_MARKERS = [
    "may",
    "permitted",
    "allowed",
    "assist",
    "support",
]

FORBIDDEN_PHRASES = [
    "workflow",
    "process",
    "tooling",
    "framework",
    "guardrail",
    "approval flow",
    "mitigate",
    "monitor",
]

def extract_section(content, section):
    pattern = rf"(?:^|\n)#\s+{re.escape(section)}\s*\n(.+?)(?=\n#\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""

def validate():
    filename = "platform_boundary_review.md"

    if not os.path.exists(filename):
        return False, (
            "platform_boundary_review.md is missing. "
            "A written platform-wide boundary definition is required."
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
                "All platform domains must be addressed."
            )

    # 2. Explicit disallowed platform zones
    if not any(m in lowered for m in DISALLOWED_MARKERS):
        return False, (
            "Explicit AI-disallowed platform boundaries are missing. "
            "Architect-level governance requires permanent exclusion zones."
        )

    # 3. Permission vs ownership distinction
    if not any(m in lowered for m in PERMISSION_MARKERS):
        return False, (
            "AI-permitted domains are not clearly articulated. "
            "Permission must be explicit and bounded."
        )

    # 4. Platform-scale reasoning
    if not any(t in lowered for t in ["future", "scale", "platform", "organization", "long-term"]):
        return False, (
            "Platform-scale reasoning is insufficient. "
            "Boundaries must constrain future AI usage, not just current systems."
        )

    # 5. Governance defensibility
    if not any(t in lowered for t in ["executive", "legal", "regulatory", "audit", "defensible"]):
        return False, (
            "Governance defensibility is insufficiently addressed. "
            "Platform boundaries must survive executive and regulatory scrutiny."
        )

    # 6. Reject procedural framing
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            return False, (
                "Procedural or mitigation language detected. "
                "This lab evaluates boundary definition, not governance enforcement."
            )

    return True, (
        "Platform-wide AI boundaries defined successfully. "
        "The analysis reflects Architect-level governance judgment."
    )

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
