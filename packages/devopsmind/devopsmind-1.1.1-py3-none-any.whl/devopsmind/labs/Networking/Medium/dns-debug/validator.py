#!/usr/bin/env python3
import subprocess
import os

def validate(context=None):
    script = "diagnose_dns.sh"

    # Check script exists (workspace-relative)
    if not os.path.exists(script):
        message = "diagnose_dns.sh missing."
        return False, message

    try:
        # ❗ FIX:
        # Do NOT use subprocess.check_output()
        # It internally calls subprocess.run(), which we sandbox,
        # causing recursion. Use subprocess.run() directly.
        result = subprocess.run(
            ["bash", script],
            capture_output=True,
            text=True,
            check=False,
        )
        out = result.stdout.strip()

    except Exception as e:
        message = f"Script failed: {e}"
        return False, message

    if out != "No DNS servers reachable":
        message = "Incorrect diagnosis."
        return False, message

    message = "DNS issue correctly diagnosed."
    return True, message


if __name__ == "__main__":
    ok, message = validate()
    print(message)
    exit(0 if ok else 1)
