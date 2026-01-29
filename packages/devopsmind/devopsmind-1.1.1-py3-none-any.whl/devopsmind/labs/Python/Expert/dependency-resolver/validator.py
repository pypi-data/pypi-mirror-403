import subprocess
import os

DEPS = {
    "build": [],
    "test": ["build"],
    "lint": ["build"],
    "package": ["test", "lint"],
    "deploy": ["package"],
}

def validate(context=None):
    script = "resolve_deps.py"

    if not os.path.exists(script):
        message = "resolve_deps.py missing."
        return False, message

    try:
        output = subprocess.check_output(
            ["python3", script],
            text=True,
            timeout=5
        ).strip().splitlines()
    except Exception as e:
        message = f"Script failed: {e}"
        return False, message

    if set(output) != set(DEPS.keys()):
        message = "Output must include all tasks exactly once."
        return False, message

    position = {task: i for i, task in enumerate(output)}

    for task, deps in DEPS.items():
        for dep in deps:
            if position[dep] >= position[task]:
                message = f"Dependency order invalid: {task} depends on {dep}"
                return False, message

    message = "Dependencies resolved in valid order."
    return True, message
