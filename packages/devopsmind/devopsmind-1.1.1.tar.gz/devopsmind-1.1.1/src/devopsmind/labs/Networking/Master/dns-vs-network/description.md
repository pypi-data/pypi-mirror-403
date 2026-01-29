# Diagnose DNS vs Network Connectivity Failure

Objective:

Diagnose whether a connectivity issue is caused by
DNS resolution failure or underlying network connectivity
using provided diagnostic evidence.

This lab focuses on judgment and layered troubleshooting,
not live network execution.

---
Requirements:

- Analysis must be based only on provided log files
- The solution must work fully offline
- A shell script must be used to produce the diagnosis

---
Task Requirements:

You are provided with two log files:

- ping.log — shows ICMP connectivity results
- dns.log — shows DNS lookup output

Create a script named diagnose_network.sh that:

1. Analyzes both log files
2. Determines whether the issue is network connectivity or DNS resolution
3. Prints exactly the following output:

Network reachable but DNS resolution failing

---
Constraints:

- Do NOT perform real network requests
- Do NOT modify system configuration
- Do NOT modify the provided log files
- Output must match exactly
