# Parse Logs and Generate Summary

Objective:

- Parse a structured application log file using Python.
- Extract log severity levels from each log entry.
- Generate a reliable summary that counts occurrences of each log level.
- Produce deterministic output suitable for automation and reporting.

---
Requirements:

- The solution must be written in Python.
- Only the Python standard library may be used.
- Input data must be read from the provided log file.
- Log parsing must be performed programmatically, not manually.
- Output must be consistent and reproducible on every run.

---
Task Requirements:

- Create a Python file named `log_parser.py`.
- Read the file `app.log` from the current directory.
- For each log entry:
  - Identify the log severity level (INFO, ERROR, WARN).
- Count how many times each severity level appears in the log file.
- Print the summary output **exactly** in the following order:
  - INFO
  - ERROR
  - WARN
- Each output line must follow this exact format:
  - `<LEVEL>: <count>`
- Each result must be printed on its own line.
- No additional text, headers, or formatting is allowed.

---
Constraints:

- Do NOT modify `app.log`.
- Do NOT hardcode expected counts or output values.
- Do NOT change the output order.
- Do NOT use external libraries or third-party modules.
- Do NOT print extra whitespace or debug output.
- Validation is execution-based and strict.

