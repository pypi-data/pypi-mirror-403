# Debug a failed DNS lookup

Objective:

Diagnose the root cause of a failed DNS lookup using
provided failure output and systematic reasoning.

This lab focuses on understanding DNS failure
modes rather than executing live network commands.

---
Requirements:

- A shell script must be written to analyze DNS failure output
- The analysis must be based only on provided evidence
- The solution must work offline and locally

---
Task Requirements:

You are provided a DNS failure log file named dns_failure.log.

Create a script named diagnose_dns.sh that:

1. Reads the contents of dns_failure.log
2. Identifies the root cause of the DNS failure
3. Prints a single-line diagnosis

The expected diagnosis output is:

No DNS servers reachable

---
Constraints:

- Do NOT perform live DNS queries
- Do NOT access the network
- Do NOT modify the provided log file
- Output must match exactly

