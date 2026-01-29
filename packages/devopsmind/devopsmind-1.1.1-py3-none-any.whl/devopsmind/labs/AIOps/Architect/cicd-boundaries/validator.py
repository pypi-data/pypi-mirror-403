import os
import re
import sys

REQUIRED_SECTIONS = [
    "CI/CD Domains Assessed",
    "AI-Disallowed CI/CD Boundaries",
    "AI-Permitted CI/CD Domains",
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
    "inform",
    "support",
    "recommend",
    "advise",
]

FORBIDDEN_PHRASES = [
    "workflow",
    "approval mechanism",
    "controls",
    "guardrails",
    "monitoring",
    "tooling",
    "framework",
]

def extract_section(content, section):
    pattern = rf"(?:^|\n)#\s+{re.escape(section)}\s*\n(.+?)(?=\n#\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""

def validate():
    filename = "cicd_boundary_review.md"

    if not os.path.exists(filename):
        return False, (
            "cicd_boundary_review.md is missing. "
            "A written CI/CD boundary definition is required."
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

    # 2. Explicit disallowed CI/CD zones
    if not any(m in lowered for m in DISALLOWED_MARKERS):
        return False, (
            "Explicit AI-disallowed CI/CD boundaries are missing. "
            "Architect-level governance requires permanent exclusion zones."
        )

    # 3. Support vs execution distinction
    if not any(m in lowered for m in SUPPORT_MARKERS):
        return False, (
            "AI-permitted support domains are not clearly distinguished "
            "from CI/CD execution or promotion authority."
        )

    # 4. Governance defensibility
    if not any(t in lowered for t in ["executive", "regulatory", "audit", "legal", "defensible"]):
        return False, (
            "Governance defensibility is insufficiently addressed. "
            "Boundaries must survive regulatory and executive scrutiny."
        )

    # 5. Reject procedural framing
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            return False, (
                "Procedural or enforcement-focused language detected. "
                "This lab evaluates boundary definition, not implementation."
            )

    return True, (
        "CI/CD boundaries defined successfully. "
        "The analysis reflects Architect-level governance judgment."
    )

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
