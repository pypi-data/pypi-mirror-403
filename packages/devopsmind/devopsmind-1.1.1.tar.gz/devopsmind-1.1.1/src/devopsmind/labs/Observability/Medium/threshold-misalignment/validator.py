import os

def is_placeholder(text):
    """
    Detect unchanged guidance text or empty content.
    """
    placeholders = [
        "describe how the alert threshold compares to observed metrics",
        "explain whether the alert fires too early",
        "too late",
        "or at an appropriate time",
    ]
    return len(text.strip()) == 0 or any(p in text for p in placeholders)

def validate():
    if not os.path.exists("threshold-evaluation.md"):
        return False, "threshold-evaluation.md not found."

    content = open("threshold-evaluation.md").read().lower()

    # Fail if learner left the template unchanged
    if is_placeholder(content):
        return False, "Threshold evaluation has not been completed."

    # Must reference threshold behavior
    if "threshold" not in content:
        return False, "Threshold behavior is not discussed."

    # Must reference metrics
    if not any(word in content for word in ["latency", "metric", "response time"]):
        return False, "Metrics are not referenced."

    # Must make a judgment about timing
    if not any(
        word in content
        for word in ["early", "late", "appropriate", "too sensitive", "too strict"]
    ):
        return False, "Threshold timing judgment is missing."

    return True, "Alert threshold alignment evaluated correctly."
