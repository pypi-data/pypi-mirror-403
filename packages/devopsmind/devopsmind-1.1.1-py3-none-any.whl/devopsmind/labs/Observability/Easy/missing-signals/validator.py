import os

def is_placeholder(text):
    """
    Detect unchanged guidance text or empty content.
    """
    placeholders = [
        "describe what information the logs provide",
        "identify which important signals or details are missing",
        "would limit understanding",
    ]
    return len(text.strip()) == 0 or any(p in text for p in placeholders)

def validate():
    if not os.path.exists("signal-gaps.md"):
        return False, "signal-gaps.md not found."

    content = open("signal-gaps.md").read().lower()

    # Fail if learner left the template unchanged
    if is_placeholder(content):
        return False, "Signal gap analysis has not been completed."

    # Ensure learner discusses absence
    if not any(word in content for word in ["missing", "not available", "no data", "lack"]):
        return False, "Analysis must identify missing or absent signals."

    # Ensure learner references logs
    if "log" not in content:
        return False, "Analysis must reference the provided logs."

    # Prevent diagnosis or RCA
    forbidden = ["root cause", "caused by", "failure reason", "incident"]
    if any(word in content for word in forbidden):
        return False, "Analysis should not diagnose causes or incidents."

    return True, "Missing observability signals correctly identified."
