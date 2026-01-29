def validate(submission: str):
    required_sections = [
        "Governance Override Assessment",
        "Risk Introduced by Authority Pressure",
        "Accountability Under Override Conditions",
        "Removal Decision",
        "Governance Defensibility",
    ]

    missing = [s for s in required_sections if s not in submission]
    if missing:
        return False, f"Missing required sections: {', '.join(missing)}."

    text = submission.strip().lower()

    if len(text) < 1400:
        return False, "Master-level governance override decisions require deep reasoning."

    banned = [
        "mitigate",
        "escalate",
        "policy",
        "committee",
        "process change",
        "controls",
        "oversight",
        "framework",
    ]

    for term in banned:
        if term in text:
            return False, "Mitigation or governance-repair language is not allowed."

    if "remove" not in text and "retain" not in text:
        return False, "A clear remove-or-retain decision is required."

    if "override" not in text and "pressure" not in text:
        return False, "Governance override pressure must be explicitly addressed."

    if "defens" not in text:
        return False, "Governance defensibility is insufficiently addressed."

    return True, "Submission reflects Master-level governance override judgment."
