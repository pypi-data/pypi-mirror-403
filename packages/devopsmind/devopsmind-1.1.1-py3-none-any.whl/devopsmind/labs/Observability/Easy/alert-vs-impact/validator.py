import os

def is_placeholder(text):
    """
    Detect unchanged guidance text.
    """
    placeholders = [
        "describe what the alerts indicate",
        "explain whether the alerts alone confirm user-facing impact",
        "and why or why not",
    ]
    return len(text.strip()) == 0 or any(p in text for p in placeholders)

def validate():
    if not os.path.exists("impact-assessment.md"):
        return False, "impact-assessment.md not found."

    content = open("impact-assessment.md").read().lower()

    # Fail if learner left the template unchanged
    if is_placeholder(content):
        return False, "Impact assessment has not been completed."

    # Must reference alerts
    if "alert" not in content:
        return False, "Assessment must reference alerts."

    # Must discuss impact
    if "impact" not in content:
        return False, "Assessment must discuss user impact."

    # Must state uncertainty clearly
    if not any(
        phrase in content
        for phrase in [
            "not confirmed",
            "does not confirm",
            "no evidence",
            "cannot conclude",
            "not enough information",
        ]
    ):
        return False, "Assessment must clearly state that impact cannot be confirmed from alerts alone."

    return True, "Alert meaning and user impact correctly distinguished."
