# Reconstruct Network Incident Timeline

Objective:

- Analyze a simulated production network incident using multiple log sources.
- Reconstruct the sequence of events that led to an application outage.
- Practice expert-level incident correlation without executing live commands.

---
Requirements:

- Three log files are provided in the working directory:
  - firewall.log
  - dns.log
  - app.log
- The solution must be implemented as a shell script named timeline.sh.
- The analysis must be based only on the provided logs.

---
Task Requirements:

- Read and analyze all provided log files.
- Identify the earliest failure event.
- Determine how subsequent events are causally related.
- Correlate timestamps across logs to reconstruct the incident sequence.
- Output exactly the following timeline, in order:
  - 10:01 DNS failure detected
  - 10:02 Firewall rule change applied
  - 10:03 Application outage occurred

---
Constraints:

- Do NOT run live network commands.
- Do NOT modify the provided log files.
- Do NOT access the network.
- Do NOT add additional output or commentary.
- Validation is static and based solely on script output.

