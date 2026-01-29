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

    # Package installation check (structure-based)
    pkg_tasks = [
        t for t in tasks
        if isinstance(t, dict) and any(m in t for m in ("package", "apt", "yum"))
    ]

    if not pkg_tasks:
        return False, "No package management task found."

    pkg_ok = False
    for task in pkg_tasks:
        module = list(task.keys())[0]
        params = task.get(module, {})
        if isinstance(params, dict) and params.get("name") == "tree":
            pkg_ok = True

    if not pkg_ok:
        return False, "Package task must manage the 'tree' package."

    # File creation / content check
    file_tasks = [
        t for t in tasks
        if isinstance(t, dict) and "copy" in t
    ]

    if not file_tasks:
        return False, "No file content management task found."

    file_ok = False
    for task in file_tasks:
        copy_cfg = task.get("copy", {})
        if (
            copy_cfg.get("dest") == "/tmp/info.txt"
            and copy_cfg.get("content") == "Ansible Works"
        ):
            file_ok = True

    if not file_ok:
        return False, (
            "A copy task must create /tmp/info.txt "
            "with content exactly 'Ansible Works'."
        )

    return True, "Ansible playbook demonstrates correct package and file management."

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
