# Extract Unique ERROR Logs

Objective:

- Practice extracting structured information from log files using Linux command-line tools.
- Understand how log pipelines are built by combining filtering, field selection, sorting, and deduplication.
- Learn how to produce clean, deterministic output suitable for review or automation.

---
Requirements:

- A log file named app.log is provided in the working directory.
- The solution must produce an output file named errors.txt.
- The output must be derived only from the contents of app.log.

---
Task Requirements:

- Read the provided app.log file.
- Extract only log lines with the ERROR log level.
- Remove duplicate ERROR entries so that each unique error appears only once.
- Sort the remaining entries chronologically based on their timestamp.
- Output only the timestamp and the error message, excluding the log level.
- Write the final result to a file named errors.txt.

---
Constraints:

- Do not modify the original app.log file.
- Do not include INFO or other non-error log entries.
- Do not include the log level in the output.
- Validation is performed by static inspection of the generated errors.txt file.

