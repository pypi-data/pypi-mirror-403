# Design a safe cleanup script with dry-run

Objective:

- Design a Bash script that safely identifies files eligible for cleanup.
- Understand how dry-run modes prevent accidental data loss.
- Learn how defensive scripting patterns protect production systems.

---
Requirements:

- A directory named workspace is provided in the working directory.
- The solution must be implemented as a Bash script named cleanup.sh.
- The script must support a --dry-run argument.

---
Task Requirements:

- Create a script named cleanup.sh.
- Accept a command-line argument named --dry-run.
- When run with --dry-run, identify files ending with the .tmp extension.
- Print the names of files that would be deleted, one per line.
- Ensure no files are deleted when running in dry-run mode.

---
Constraints:

- Do not delete any files during validation.
- Do not modify files in the workspace directory.
- Do not print additional text or explanations.
- Validation is performed by executing the script with --dry-run and inspecting its output.
