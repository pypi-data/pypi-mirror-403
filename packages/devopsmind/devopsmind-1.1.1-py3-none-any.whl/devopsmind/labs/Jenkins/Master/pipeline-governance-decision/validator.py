from pathlib import Path

def validate():
    """
    Master-level Jenkins CI governance policy validation.

    Guarantees:
    - Never crashes
    - Always returns (bool, message)
    - Requires real policy decisions, not templates
    """

    policy_path = Path("ci-policy.md")

    # --- File existence ---
    if not policy_path.exists():
        return False, (
            "CI governance policy not found.\n"
            "The file `ci-policy.md` must be completed before validation."
        )

    # --- Safe read ---
    try:
        policy = policy_path.read_text()
    except Exception:
        return False, (
            "Unable to read `ci-policy.md`.\n"
            "Ensure the file exists and is readable."
        )

    required_sections = [
        "Scope",
        "Governance Rules",
        "Rule 1",
        "Rule 2",
        "Rule 3",
        "Review Considerations",
    ]

    # --- Structural validation ---
    for section in required_sections:
        if section not in policy:
            return False, (
                f"Missing required section: {section}.\n"
                "A governance policy must follow a complete reviewable structure."
            )

    # --- Placeholder detection ---
    placeholders = [
        "Describe which pipelines",
        "Description:",
        "Justification:",
        "Explain how this policy",
    ]

    for placeholder in placeholders:
        if placeholder in policy:
            return False, (
                "The governance policy still contains placeholder text.\n"
                "Master-level labs require fully articulated decisions."
            )

    # --- Depth validation ---
    non_empty_lines = [
        line for line in policy.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    if len(non_empty_lines) < 20:
        return False, (
            "The governance policy lacks sufficient depth.\n"
            "Master-level submissions must demonstrate clear scope, rules, and reasoning."
        )

    return True, (
        "Governance policy is complete and review-ready.\n"
        "The rules, scope, and justifications demonstrate senior-level judgment."
    )
