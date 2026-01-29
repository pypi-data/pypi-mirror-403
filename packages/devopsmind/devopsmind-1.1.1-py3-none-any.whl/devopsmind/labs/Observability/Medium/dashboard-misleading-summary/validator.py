import os

def is_placeholder(text):
    """
    Detect unchanged guidance text or empty content.
    """
    placeholders = [
        "summarize what the dashboard indicates",
        "compare this with what the raw metrics show",
        "explain why the dashboard summary may not fully represent system behavior",
    ]
    return len(text.strip()) == 0 or any(p in text for p in placeholders)

def validate():
    if not os.path.exists("dashboard-review.md"):
        return False, "dashboard-review.md not found."

    content = open("dashboard-review.md").read().lower()

    # Fail if learner left the template unchanged
    if is_placeholder(content):
        return False, "Dashboard review has not been completed."

    # Must reference both dashboard and metrics
    if "dashboard" not in content:
        return False, "Dashboard summary is not discussed."

    if not any(word in content for word in ["metric", "latency", "throughput", "error rate"]):
        return False, "Raw metrics are not discussed."

    # Must identify misleading aspect
    if not any(word in content for word in ["misleading", "hide", "mask", "not fully", "oversimpl"]):
        return False, "Review does not explain why the dashboard may be misleading."

    return True, "Dashboard summary evaluated against raw metrics correctly."
