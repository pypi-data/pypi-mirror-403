#!/usr/bin/env python3
import subprocess
import os

EXPECTED_OUTPUT = "Network reachable but DNS resolution failing"

def validate(context=None):
    script = "diagnose_network.sh"
    ping_log = "ping.log"
    dns_log = "dns.log"

    if not os.path.exists(script):
        message = "diagnose_network.sh is missing."
        return False, message

    if not os.path.exists(ping_log):
        message = "ping.log is missing."
        return False, message

    if not os.path.exists(dns_log):
        message = "dns.log is missing."
        return False, message

    try:
        output = subprocess.check_output(
            ["bash", script],
            text=True,
            timeout=5
        ).strip()
    except Exception as e:
        message = f"Script execution failed: {e}"
        return False, message

    if output != EXPECTED_OUTPUT:
        message = f"Expected output: '{EXPECTED_OUTPUT}'"
        return False, message

    message = "Correct diagnosis of DNS vs network connectivity."
    return True, message

if __name__ == "__main__":
    ok, message = validate()
    print(message)
