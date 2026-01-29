#!/usr/bin/env python3
import os
import sys

def validate():
    # Required file check
    if not os.path.exists("decision.txt"):
        return False, "decision.txt not found."

    try:
        content = open("decision.txt").read().lower()
    except Exception:
        return False, "Unable to read decision.txt."

    # Core reasoning expectations for Medium level
    reasoning_checks = {
        "cpu_alerts": ["cpu"],
        "disk_alerts": ["disk"],
        "duplication": ["duplicate", "repeated", "same", "noise", "dedupe"],
        "prioritization": ["priority", "prioritize", "critical", "important", "impact"]
    }

    for reason, keywords in reasoning_checks.items():
        if not any(k in content for k in keywords):
            return False, f"Missing reasoning element: {reason.replace('_', ' ')}"

    # Medium-level sanity check:
    # Ensure learner distinguishes repetition vs distinct signal
    if content.count("cpu") > 1 and not any(k in content for k in ["duplicate", "repeated", "noise", "dedupe"]):
        return False, "Repeated CPU alerts should be identified as duplication or noise."

    return True, "Alert fatigue reasoning correct."

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
