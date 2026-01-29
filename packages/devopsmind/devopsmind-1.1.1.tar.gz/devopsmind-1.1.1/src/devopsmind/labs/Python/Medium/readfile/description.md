# File Reader CLI

Objective:

- Practice writing a simple Python command-line program.
- Learn how to read command-line arguments and perform file input/output.
- Produce exact stdout output suitable for use in scripts and pipelines.

---
Requirements:

- A Python script must be written to act as a CLI tool.
- The script must accept a file path as a command-line argument.
- The file contents must be printed exactly as they appear.

---
Task Requirements:

- Create a Python script named readfile.py.
- The script must accept exactly one argument: a filename.
- When executed, the script must open the specified file.
- The script must print the full contents of the file to stdout.
- No extra text, formatting, or logging may be printed.
- If the file does not exist, the script must exit with a non-zero status.

---
Constraints:

- Do NOT modify the validator.
- Do NOT print error messages or stack traces.
- Do NOT use external libraries.
- Validation is performed by executing the script and comparing stdout exactly.

