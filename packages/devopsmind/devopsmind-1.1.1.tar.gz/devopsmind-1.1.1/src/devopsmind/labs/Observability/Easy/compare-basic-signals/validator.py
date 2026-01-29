import os

def is_placeholder(text):
    """
    Detect unchanged guidance text or empty content.
    """
    placeholders = [
        "describe what the logs indicate",
        "describe what the metrics indicate",
        "describe what the alerts indicate",
        "explain where the signals align",
        "without drawing conclusions",
    ]
    return len(text.strip()) == 0 or any(p in text for p in placeholders)

def validate():
    if not os.path.exists("signal-comparison.md"):
        return False, "signal-comparison.md not found."

    content = open("signal-comparison.md").read().lower()

    # Fail if learner left the template unchanged
    if is_placeholder(content):
        return False, "Signal comparison has not been completed."

    # Ensure all signal types are discussed
    for term in ["log", "metric", "alert"]:
        if term not in content:
            return False, f"Comparison must reference {term}s."

    # Ensure comparison language is used
    if not any(word in content for word in ["compare", "align", "differ", "contrast", "similar", "different"]):
        return False, "Signals are not compared explicitly."

    # Prevent diagnosis or escalation
    forbidden = ["root cause", "incident", "failure due to", "outage", "cause"]
    if any(word in content for word in forbidden):
        return False, "Comparison should not escalate to diagnosis or incident conclusions."

    return True, "Basic observability signals correctly compared."
