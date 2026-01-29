import os

def is_placeholder(text):
    """
    Detect unchanged guidance text or empty content.
    """
    placeholders = [
        "describe which alerts indicate a real system failure",
        "explain why the remaining alerts do not represent a failure condition",
    ]
    return len(text.strip()) == 0 or any(p in text for p in placeholders)

def validate():
    # Correct filename
    if not os.path.exists("severity-assessment.md"):
        return False, "severity-assessment.md not found."

    content = open("severity-assessment.md").read().lower()

    # Fail if learner left the template unchanged
    if is_placeholder(content):
        return False, "Severity assessment has not been completed."

    # Must identify error conditions
    if "error" not in content:
        return False, "Assessment must identify error conditions."

    # Must discuss warning signals
    if "warning" not in content:
        return False, "Assessment must discuss warning signals."

    # Must clearly distinguish failure vs non-failure
    if not any(
        phrase in content
        for phrase in [
            "not a failure",
            "does not indicate failure",
            "not necessarily a failure",
            "risk but not failure",
        ]
    ):
        return False, "Assessment must clearly distinguish risk from failure."

    return True, "Alert severity correctly interpreted."
