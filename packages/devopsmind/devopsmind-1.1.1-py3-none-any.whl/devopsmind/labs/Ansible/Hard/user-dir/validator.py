#!/usr/bin/env python3
import yaml
import os
import sys

def validate():
    if not os.path.exists("playbook.yml"):
        return False, "playbook.yml is missing."

    try:
        with open("playbook.yml", encoding="utf-8") as f:
            plays = yaml.safe_load(f)
    except Exception as e:
        return False, f"Invalid YAML: {e}"

    if not isinstance(plays, list) or not plays:
        return False, "playbook.yml must contain at least one play."

    play = plays[0]
    tasks = play.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return False, "Play must contain a list of tasks."

    user_ok = False
    dir_ok = False

    for task in tasks:
        if not isinstance(task, dict):
            continue

        if "user" in task:
            user_cfg = task.get("user", {})
            if isinstance(user_cfg, dict) and user_cfg.get("name") == "deploy":
                user_ok = True

        if "file" in task:
            file_cfg = task.get("file", {})
            if (
                isinstance(file_cfg, dict)
                and file_cfg.get("path") == "/opt/deploy"
                and file_cfg.get("state") == "directory"
                and file_cfg.get("owner") == "deploy"
                and str(file_cfg.get("mode")) in ("0755", "755")
            ):
                dir_ok = True

    if not user_ok:
        return False, "User task ensuring 'deploy' exists is missing."

    if not dir_ok:
        return False, (
            "Directory task for /opt/deploy with owner 'deploy' "
            "and mode 0755 is missing or incorrect."
        )

    return True, "Ansible playbook enforces idempotent user and directory state."

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
