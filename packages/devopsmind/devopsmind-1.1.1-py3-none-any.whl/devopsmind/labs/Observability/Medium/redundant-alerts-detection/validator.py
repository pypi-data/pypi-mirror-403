import os

def is_placeholder(text):
    """
    Detect unchanged guidance text or empty content.
    """
    placeholders = [
        "list the alerts that appear to represent the same underlying condition",
        "explain why these alerts are redundant",
        "how they could increase noise",
    ]
    return len(text.strip()) == 0 or any(p in text for p in placeholders)

def validate():
    if not os.path.exists("redundancy-assessment.md"):
        return False, "redundancy-assessment.md not found."

    content = open("redundancy-assessment.md").read().lower()

    # Fail if learner left the template unchanged
    if is_placeholder(content):
        return False, "Redundancy assessment has not been completed."

    # Must identify redundancy
    if not any(word in content for word in ["redundant", "duplicate", "overlap", "same"]):
        return False, "Redundant alerts are not clearly identified."

    # Must reference multiple alerts
    if content.count("alert") < 2:
        return False, "Assessment must reference multiple alerts."

    # Must explain impact of redundancy
    if not any(word in content for word in ["noise", "fatigue", "overwhelm"]):
        return False, "Impact of redundancy is not explained."

    return True, "Redundant alerts correctly identified."
