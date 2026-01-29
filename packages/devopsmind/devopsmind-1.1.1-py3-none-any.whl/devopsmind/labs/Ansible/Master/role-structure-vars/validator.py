#!/usr/bin/env python3
import os
import yaml
import sys

def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate():
    defaults_path = "roles/web/defaults/main.yml"
    tasks_path = "roles/web/tasks/main.yml"

    if not os.path.exists(defaults_path):
        return False, "roles/web/defaults/main.yml is missing."

    if not os.path.exists(tasks_path):
        return False, "roles/web/tasks/main.yml is missing."

    try:
        defaults_data = load_yaml(defaults_path)
    except Exception as e:
        return False, f"Invalid YAML in defaults: {e}"

    if not isinstance(defaults_data, dict) or "app_port" not in defaults_data:
        return False, "Role defaults must define an 'app_port' variable."

    try:
        tasks_data = load_yaml(tasks_path)
    except Exception as e:
        return False, f"Invalid YAML in tasks: {e}"

    if not isinstance(tasks_data, list) or not tasks_data:
        return False, "tasks/main.yml must contain at least one task."

    variable_used = False
    for task in tasks_data:
        if not isinstance(task, dict):
            continue
        debug_cfg = task.get("debug")
        if isinstance(debug_cfg, dict):
            msg = debug_cfg.get("msg", "")
            if "{{ app_port }}" in msg:
                variable_used = True

    if not variable_used:
        return False, "At least one task must reference the app_port variable."

    return True, "Ansible role demonstrates correct variable-driven design."

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
