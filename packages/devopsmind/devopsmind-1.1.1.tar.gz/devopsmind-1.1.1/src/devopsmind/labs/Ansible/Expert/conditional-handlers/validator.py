#!/usr/bin/env python3
import os
import yaml
import sys

def validate():
    path = "playbook.yml"

    if not os.path.exists(path):
        return False, "playbook.yml is missing."

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return False, f"Invalid YAML: {e}"

    if not isinstance(data, list) or not data:
        return False, "playbook.yml must contain at least one play."

    play = data[0]
    tasks = play.get("tasks")
    handlers = play.get("handlers")

    if not isinstance(tasks, list) or not tasks:
        return False, "No tasks defined."

    if not isinstance(handlers, list) or not handlers:
        return False, "No handlers defined."

    # At least one conditional task that notifies a handler
    conditional_notify = False
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if "when" in task and "notify" in task:
            conditional_notify = True

    if not conditional_notify:
        return False, (
            "At least one task must execute conditionally "
            "and notify a handler."
        )

    # Handlers must exist and be non-destructive
    valid_handler = False
    for handler in handlers:
        if not isinstance(handler, dict):
            continue
        if "debug" in handler:
            valid_handler = True

    if not valid_handler:
        return False, "At least one handler must use a non-destructive action (e.g. debug)."

    return True, "Expert-level conditional and handler control flow detected."

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
