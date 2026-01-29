import os

def is_placeholder(text):
    """
    Detect unchanged guidance text or empty content.
    """
    placeholders = [
        "summarize what the alerts indicate",
        "explain whether these alerts pose a risk",
        "to the defined slos",
        "and why or why not",
    ]
    return len(text.strip()) == 0 or any(p in text for p in placeholders)

def validate():
    if not os.path.exists("slo-impact-assessment.md"):
        return False, "slo-impact-assessment.md not found."

    content = open("slo-impact-assessment.md").read().lower()

    # Fail if learner left the template unchanged
    if is_placeholder(content):
        return False, "SLO impact assessment has not been completed."

    # Must reference SLO
    if not any(word in content for word in ["slo", "service level objective", "objective"]):
        return False, "SLO is not referenced."

    # Must reference alerts
    if "alert" not in content:
        return False, "Alerts are not discussed."

    # Must make an impact judgment
    if not any(
        word in content
        for word in [
            "risk",
            "impact",
            "does not threaten",
            "within",
            "breach",
            "violate",
        ]
    ):
        return False, "SLO impact judgment is missing."

    return True, "Alert impact evaluated correctly against SLOs."
