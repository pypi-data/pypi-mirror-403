#!/usr/bin/env python3
import os
import re
import sys

REQUIRED_SECTIONS = [
    "Final Decision",
    "Current Value Assessment",
    "Risk Analysis",
    "Cost & Maintenance",
    "Replacement Strategy",
    "Long-Term Impact",
]

FORBIDDEN_PHRASES = [
    "ai will improve over time",
    "future model upgrades",
    "better prompts",
    "fully autonomous",
    "self-healing",
]

DECISION_TERMS = {
    "decommission": r"\bdecommission\b|\bdecommissioned\b",
    "retain": r"\bretain\b|\bretained\b",
    "reduce": r"\breduce\b|\breduced\b",
}

def extract_section(content, section):
    pattern = rf"(?:^|\n)##\s+{re.escape(section)}\s*\n(.+?)(?=\n##\s+|\Z)"
    match = re.search(pattern, content, re.S | re.I)
    return match.group(1).strip() if match else ""

def validate():
    if not os.path.exists("decommission_plan.md"):
        return False, (
            "decommission_plan.md is missing. "
            "This lab requires a written evaluation document."
        )

    with open("decommission_plan.md", encoding="utf-8") as f:
        content = f.read()

    lowered = content.lower()

    # 1. Section presence
    for section in REQUIRED_SECTIONS:
        body = extract_section(content, section)
        if not body:
            return False, (
                f"The section '{section}' is missing or empty. "
                "Each section should contain a thoughtful assessment."
            )

    # 2. Final decision clarity (FIXED)
    final_decision = extract_section(content, "Final Decision").lower()

    matched_decisions = [
        name for name, pattern in DECISION_TERMS.items()
        if re.search(pattern, final_decision)
    ]

    if len(matched_decisions) == 0:
        return False, (
            "A clear final decision is missing. "
            "The Final Decision section must explicitly state whether the system is "
            "retained, reduced, or decommissioned."
        )

    if len(matched_decisions) > 1:
        return False, (
            "Multiple conflicting decisions were detected in the Final Decision section. "
            "The evaluation must converge on a single outcome."
        )

    # 3. Strategic framing check
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            return False, (
                "Future-looking AI improvement justification detected. "
                "This lab focuses on evaluating the system as it exists today."
            )

    # 4. Replacement strategy sanity
    replacement_text = extract_section(content, "Replacement Strategy").lower()
    if re.search(r"\bai\b", replacement_text):
        return False, (
            "AI-based replacements were detected in the replacement strategy. "
            "The lab asks for deterministic or non-AI alternatives only."
        )

    return True, (
        "Evaluation completed successfully. "
        "The analysis demonstrates clear decision-making and strategic reasoning."
    )

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
