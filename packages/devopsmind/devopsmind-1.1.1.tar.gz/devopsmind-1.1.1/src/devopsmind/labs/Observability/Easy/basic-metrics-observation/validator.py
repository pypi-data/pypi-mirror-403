import os

def is_placeholder(text):
    """
    Detect unchanged guidance text or empty content.
    """
    placeholders = [
        "describe any visible trends",
        "focus on how the values change",
        "not on possible causes",
    ]
    return len(text.strip()) == 0 or any(p in text for p in placeholders)

def validate():
    if not os.path.exists("metrics-observation.md"):
        return False, "metrics-observation.md not found."

    content = open("metrics-observation.md").read().lower()

    # Fail if learner left the template unchanged
    if is_placeholder(content):
        return False, "Metrics observation has not been completed."

    # Ensure trends are described
    if not any(word in content for word in ["increase", "increasing", "rise", "rising", "trend"]):
        return False, "Metrics trends are not clearly described."

    # Ensure both metrics are mentioned
    if "cpu" not in content or "memory" not in content:
        return False, "Both CPU and memory metrics must be discussed."

    # Prevent root cause speculation
    forbidden = ["because", "caused by", "due to"]
    if any(word in content for word in forbidden):
        return False, "Observation should not speculate on causes."

    return True, "Metrics were observed and described correctly."
