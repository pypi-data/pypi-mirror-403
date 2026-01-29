import os

def is_placeholder(text):
    """
    Detect unchanged guidance text or empty content.
    """
    placeholders = [
        "list the alert",
        "require immediate attention",
        "explain why these alerts take precedence",
        "remaining alerts are lower priority",
    ]
    return len(text.strip()) == 0 or any(p in text for p in placeholders)

def validate():
    if not os.path.exists("priority-assessment.md"):
        return False, "priority-assessment.md not found."

    content = open("priority-assessment.md").read().lower()

    # Fail if learner left the template unchanged
    if is_placeholder(content):
        return False, "Priority assessment has not been completed."

    # Must clearly identify highest priority
    if not any(word in content for word in ["immediate", "highest priority", "top priority", "critical"]):
        return False, "Assessment does not clearly identify the highest-priority alert."

    # Must reference critical service / alert explicitly
    if not any(word in content for word in ["payment", "checkout", "service unavailable", "unavailable"]):
        return False, "Assessment does not identify the most critical service alert."

    # Must explicitly de-prioritize other alerts
    if not any(word in content for word in ["lower priority", "less urgent", "secondary", "can wait", "deprioritized"]):
        return False, "Lower-priority alerts are not clearly explained."

    return True, "Alert prioritization demonstrated correctly."
