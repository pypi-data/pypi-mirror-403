import os

def validate():
    if not os.path.exists("decision-log.md"):
        return False, "decision-log.md not found."

    content = open("decision-log.md").read().lower()

    required_sections = [
        "situation overview",
        "decision",
        "rationale",
        "risks and trade-offs",
    ]

    for section in required_sections:
        if section not in content:
            return False, f"Missing section: {section.title()}"

    # Must make an explicit decision
    if not any(word in content for word in ["escalate", "contain"]):
        return False, "Decision to escalate or contain is not clearly stated."

    # Must justify decision
    if not any(word in content for word in ["because", "due to", "based on"]):
        return False, "Decision rationale is not clearly explained."

    # Must show risk awareness
    if not any(word in content for word in ["risk", "trade-off", "impact", "uncertainty"]):
        return False, "Risk and trade-off awareness is missing."

    # Must avoid premature fixes
    forbidden = ["deploy", "code change", "restart service"]
    if any(word in content for word in forbidden):
        return False, "Decision includes premature fix actions."

    return True, "Containment vs escalation decision demonstrates sound judgment."
