# Analyze Logs and Generate Summary

Objective:

- Build a Bash script that summarizes log data into a concise report.
- Understand how raw log entries can be transformed into aggregated metrics.
- Demonstrate mastery of deterministic text-processing pipelines.

---
Requirements:

- A file named system.log is provided in the working directory.
- The solution must be implemented as a Bash script named analyze_logs.sh.
- The script must be executable and runnable from the command line.

---
Task Requirements:

- Create a script named analyze_logs.sh.
- Read and process the contents of system.log.
- Extract the log level field from each log entry.
- Count how many times each log level appears.
- Produce output in the following exact order:
  - INFO: <count>
  - WARN: <count>
  - ERROR: <count>
- Print one summary line per log level and no additional output.

---
Constraints:

- Do not modify the system.log file.
- Do not hardcode counts or log level values.
- Do not change the output order or formatting.
- Validation is performed by executing the script and inspecting its output.

