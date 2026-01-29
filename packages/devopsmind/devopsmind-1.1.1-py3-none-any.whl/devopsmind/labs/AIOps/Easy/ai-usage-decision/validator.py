#!/usr/bin/env python3
import os
import re
import sys

REQUIRED_SECTIONS = [
    "Decision",
    "Rationale",
    "Risks",
    "Alternative"
]

DECISION_TERMS = ["yes", "no"]

RISK_MARKERS = [
    "risk",
    "failure",
    "uncertainty",
    "error",
    "impact",
]

ACCOUNTABILITY_TERMS = [
    "human",
    "engineer",
    "responsib",
    "accountab",
    "owned",
]

FORBIDDEN_TERMS = [
    "autonomous",
    "self-healing",
    "auto-remediate",
    "without approval",
]

def extract_section(content, section):
    pattern = rf"## {re.escape(section)}\n(.+?)(?=\n## |\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""

def is_substantive(text):
    sentences = re.split(r"[.!?]", text)
    meaningful = [s for s in sentences if len(s.strip()) > 15]
    return len(meaningful) >= 2

def validate():
    if not os.path.exists("decision.md"):
        return False, "decision.md file is missing."

    with open("decision.md", encoding="utf-8") as f:
        content = f.read()

    lowered = content.lower()

    # 1. Required sections
    for section in REQUIRED_SECTIONS:
        body = extract_section(content, section)
        if not body:
            return False, f"Section '{section}' is missing or empty."
        if not is_substantive(body):
            return False, (
                f"Section '{section}' lacks clear reasoning. "
                "Brief but meaningful judgment is expected."
            )

    # 2. Explicit YES / NO decision
    decision = extract_section(content, "Decision").lower()
    if not any(term in decision for term in DECISION_TERMS):
        return False, "Decision must explicitly state YES or NO."

    # 3. Risk awareness
    if not any(term in lowered for term in RISK_MARKERS):
        return False, (
            "Risk awareness is missing. "
            "AI usage decisions must acknowledge operational risk."
        )

    # 4. Human accountability
    if not any(term in lowered for term in ACCOUNTABILITY_TERMS):
        return False, (
            "Human accountability is not clearly stated. "
            "AI must not replace human responsibility."
        )

    # 5. Safety guard
    for term in FORBIDDEN_TERMS:
        if term in lowered:
            return False, (
                "Unsafe autonomy detected. "
                "AI must not operate without human control."
            )

    return True, "AI usage decision demonstrates clear judgment and accountability."

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
