#!/usr/bin/env python3
import yaml
import os
import sys

def validate():
    if not os.path.exists("playbook.yml"):
        return False, "playbook.yml is missing."

    try:
        with open("playbook.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return False, f"Invalid YAML: {e}"

    if not isinstance(data, list) or not data:
        return False, "playbook.yml must contain at least one play."

    play = data[0]
    tasks = play.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return False, "The play must define at least one task."

    debug_tasks = [t for t in tasks if isinstance(t, dict) and "debug" in t]
    if not debug_tasks:
        return False, "At least one task must use the debug module."

    debug_cfg = debug_tasks[0].get("debug")
    if not isinstance(debug_cfg, dict) or "msg" not in debug_cfg:
        return False, "The debug task must define a 'msg' field."

    return True, "Basic Ansible playbook structure is valid."

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
