from pathlib import Path

PLACEHOLDERS = [
    "Describe which",
    "Description:",
    "Justification:",
    "Explain how"
]

def validate():
    policy_path = Path("gitops-policy.md")

    if not policy_path.exists():
        return False, "gitops-policy.md not found"

    policy = policy_path.read_text()

    required_sections = [
        "Scope",
        "Governance Rules",
        "Rule 1",
        "Rule 2",
        "Rule 3",
        "Justification",
        "Trade-off Considerations"
    ]

    # --- Structural validation ---
    for section in required_sections:
        if section not in policy:
            return False, f"Missing required section: {section}"

    # --- Placeholder detection (MASTER-level) ---
    for placeholder in PLACEHOLDERS:
        if placeholder in policy:
            return (
                False,
                "The governance policy still contains placeholder text. "
                "Master-level labs require fully articulated decisions."
            )

    # --- Ensure multiple justifications exist ---
    if policy.count("Justification") < 3:
        return False, "Each governance rule must include a justification"

    # --- Evidence awareness ---
    text = policy.lower()

    if "shared" not in text:
        return False, "Policy must address governance of shared GitOps configuration"

    if "ownership" not in text:
        return False, "Policy must address ownership responsibility"

    return True, "GitOps governance policy is complete, clear, and senior-level"
