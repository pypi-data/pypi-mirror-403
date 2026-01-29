import os
import re
import sys

REQUIRED_SECTIONS = [
    "Data Domains Assessed",
    "AI-Disallowed Data Access Boundaries",
    "AI-Permitted Data Access Domains",
    "Boundary Rationale",
    "Governance Defensibility",
]

DISALLOWED_MARKERS = [
    "never",
    "must not",
    "disallowed",
    "prohibited",
    "cannot access",
]

PERMITTED_MARKERS = [
    "may access",
    "permitted",
    "allowed",
    "with human ownership",
]

FORBIDDEN_PHRASES = [
    "encrypt",
    "mask",
    "anonymize",
    "controls",
    "monitoring",
    "tooling",
    "framework",
]

def extract_section(content, section):
    pattern = rf"(?:^|\n)#\s+{re.escape(section)}\s*\n(.+?)(?=\n#\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""

def validate():
    filename = "data_access_boundary_review.md"

    if not os.path.exists(filename):
        return False, (
            "data_access_boundary_review.md is missing. "
            "A written data-access boundary definition is required."
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

    # 2. Explicit disallowed data domains
    if not any(m in lowered for m in DISALLOWED_MARKERS):
        return False, (
            "Explicit AI-disallowed data access boundaries are missing. "
            "Architect-level governance requires permanent exclusion zones."
        )

    # 3. Permitted vs prohibited distinction
    if not any(m in lowered for m in PERMITTED_MARKERS):
        return False, (
            "AI-permitted data access domains are not clearly distinguished "
            "from permanently disallowed domains."
        )

    # 4. Governance defensibility
    if not any(t in lowered for t in ["executive", "legal", "regulatory", "audit", "defensible"]):
        return False, (
            "Governance defensibility is insufficiently addressed. "
            "Data boundaries must survive legal and regulatory sc
