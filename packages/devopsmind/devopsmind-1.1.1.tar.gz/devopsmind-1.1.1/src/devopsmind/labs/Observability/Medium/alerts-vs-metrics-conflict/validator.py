import os

def is_placeholder(text):
    """
    Detect unchanged guidance text or empty content.
    """
    placeholders = [
        "describe how the alerts and metrics differ",
        "explain which signal you would prioritize",
        "and why that signal provides stronger evidence",
    ]
    return len(text.strip()) == 0 or any(p in text for p in placeholders)

def validate():
    if not os.path.exists("signal-priority.md"):
        return False, "signal-priority.md not found."

    content = open("signal-priority.md").read().lower()

    # Fail if learner left the template unchanged
    if is_placeholder(content):
        return False, "Signal priority assessment has not been completed."

    # Must acknowledge conflict
    if not any(word in content for word in ["conflict", "disagree", "different", "mismatch"]):
        return False, "Signal conflict is not clearly identified."

    # Must reference both alerts and metrics
    if "alert" not in content or "metric" not in content:
        return False, "Both alerts and metrics must be discussed."

    # Must make a prioritization decision
    if not any(word in content for word in ["prioritize", "priority", "focus on", "trust"]):
        return False, "No clear signal prioritization decision is made."

    return True, "Conflicting signals evaluated and prioritized correctly."
