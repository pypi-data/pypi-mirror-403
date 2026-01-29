# Generate metrics from log file

Objective:
- Build a Bash script that converts raw access log entries into aggregated metrics.
- Understand how log fields can be extracted and grouped to produce meaningful summaries.
- Demonstrate mastery of deterministic Linux text-processing pipelines.

---
Requirements:
- A file named access.log is provided in the working directory.
- The solution must be implemented as a Bash script named metrics.sh.
- The script must be executable and runnable from the command line.

---
Task Requirements:
- Create a script named metrics.sh.
- Read and process the contents of access.log.
- Extract the HTTP status code field from each log entry.
- Count how many times each status code appears.
- Sort the output numerically by status code.
- Print the results in the following exact format:
  - 200: <count>
  - 404: <count>
  - 500: <count>
- Print one metric per line and no additional output.

---
Constraints:
- Do not modify the access.log file.
- Do not hardcode counts or status codes.
- Do not change the output format or ordering.
- Validation is performed by executing the script and inspecting its output.

