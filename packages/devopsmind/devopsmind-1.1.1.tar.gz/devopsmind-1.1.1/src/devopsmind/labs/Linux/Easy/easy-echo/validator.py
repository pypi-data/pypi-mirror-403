#!/usr/bin/env python3
import os
import subprocess

def validate():
    script = "echo_hello.sh"

    if not os.path.exists(script):
        message = "echo_hello.sh is missing."
        return False, message

    if not os.access(script, os.X_OK):
        message = "echo_hello.sh is not executable. Run: chmod +x echo_hello.sh"
        return False, message

    try:
        out = subprocess.check_output(
            ["bash", script],
            stderr=subprocess.STDOUT,
            text=True
        )
    except subprocess.CalledProcessError as e:
        message = f"Script failed to run: {e.output.strip()}"
        return False, message

    if out.strip() == "Hello DevOpsMind":
        message = "Correct output!"
        return True, message

    message = f"Unexpected output: {repr(out)}"
    return False, message


if __name__ == "__main__":
    ok, message = validate()
    print(message)
