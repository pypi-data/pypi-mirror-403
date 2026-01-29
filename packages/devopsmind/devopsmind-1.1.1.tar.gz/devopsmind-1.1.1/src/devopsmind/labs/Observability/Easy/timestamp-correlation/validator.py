import os

def is_placeholder(text):
    """
    Detect unchanged guidance text or empty content.
    """
    placeholders = [
        "describe the sequence of events",
        "explain how the timing of events indicates a relationship",
        "between the failure and subsequent log entries",
    ]
    return len(text.strip()) == 0 or any(p in text for p in placeholders)

def validate():
    if not os.path.exists("event-correlation.md"):
        return False, "event-correlation.md not found."

    content = open("event-correlation.md").read().lower()

    # Fail if learner left the template unchanged
    if is_placeholder(content):
        return False, "Event correlation has not been completed."

    # Ensure learner discusses order / sequence
    if not any(word in content for word in ["sequence", "order", "first", "then", "after", "before"]):
        return False, "Event sequence is not clearly described."

    # Ensure timing is used as evidence
    if not any(word in content for word in ["time", "timestamp", "at", ":"]):
        return False, "Timing evidence is not referenced."

    # Ensure failure event is recognized
    if not any(word in content for word in ["error", "failure", "failed"]):
        return False, "Failure event is not identified."

    return True, "Event correlation based on timestamps demonstrated."
