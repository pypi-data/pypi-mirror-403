import os
import re

def normalize_header(line):
    """Normalize markdown headers like '## Scope and Safeguards' → 'scope and safeguards'"""
    return re.sub(r"^#+\s*", "", line).strip().lower()

def is_placeholder(text):
    """Detect unchanged guidance or empty sections."""
    guidance_phrases = [
        "summarize the incident and policy conflict",
        "identify applicable policies and guardrails",
        "state whether policy is enforced or temporarily overridden",
        "define limits, duration, and controls",
        "explicitly own risks introduced by this decision",
    ]
    return len(text.strip()) == 0 or any(p in text for p in guidance_phrases)

def has_substance(text, min_words=10):
    """Ensure section contains real master-level reasoning."""
    return len(text.split()) >= min_words

def validate():
    if not os.path.exists("policy-decision.md"):
        return False, "policy-decision.md not found."

    content = open("policy-decision.md").read().lower()
    lines = content.splitlines()

    required_sections = [
        "situation overview",
        "relevant policy constraints",
        "decision",
        "scope and safeguards",
        "risk ownership and accountability",
    ]

    parts = {}
    current = None

    for line in lines:
        header = normalize_header(line)
        if header in required_sections:
            current = header
            parts[current] = []
        elif current:
            parts[current].append(line.strip())

    # Ensure all required sections exist
    for section in required_sections:
        if section not in parts:
            return False, f"Missing section: {section.title()}"

    # Ensure sections are completed and substantive
    for section, lines in parts.items():
        text = " ".join(lines)
        if is_placeholder(text):
            return False, f"Section '{section.title()}' has not been completed."
        if not has_substance(text):
            return False, f"Section '{section.title()}' lacks sufficient depth."

    full_text = " ".join(" ".join(v) for v in parts.values())

    # --- Master-level intent checks (VERY loose, governance-focused) ---

    # 1. Policy / constraint awareness (not recitation)
    policy_signals = [
        "policy",
        "guardrail",
        "standard",
        "control",
        "requirement",
        "compliance",
        "regulatory",
    ]
    if not any(sig in full_text for sig in policy_signals):
        return False, "Policy or governance constraints are not clearly considered."

    # 2. Explicit authority decision (without forcing override/enforce wording)
    decision_signals = [
        "we will",
        "we will not",
        "i will",
        "i will not",
        "decide",
        "choose",
        "authorize",
        "direct",
    ]
    if not any(sig in full_text for sig in decision_signals):
        return False, "A clear policy decision is not stated."

    # 3. Scope, limits, or containment of the decision
    scope_signals = [
        "scope",
        "limit",
        "bounded",
        "temporary",
        "time",
        "duration",
        "restricted",
        "conditions",
    ]
    if not any(sig in full_text for sig in scope_signals):
        return False, "Decision scope or safeguards are not clearly defined."

    # 4. Risk ownership and accountability
    ownership_signals = [
        "risk",
        "impact",
        "exposure",
        "consequence",
        "accountable",
        "responsible",
        "ownership",
        "follow-up",
    ]
    if not any(sig in full_text for sig in ownership_signals):
        return False, "Risk ownership and accountability are not acknowledged."

    return True, "Policy decision demonstrates master-level governance judgment."
