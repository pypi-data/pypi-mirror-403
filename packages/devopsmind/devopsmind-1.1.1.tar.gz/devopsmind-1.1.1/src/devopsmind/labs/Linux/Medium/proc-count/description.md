# Count Running Processes

Objective:

- Practice writing a Bash script that inspects the current system state.
- Understand how Linux exposes running processes through command-line tools.
- Learn how to produce clean, numeric output suitable for automation and monitoring.

---
Requirements:

- The task must be completed using a Bash script named count_procs.sh.
- The script must be executable and runnable from the command line.
- Output must be written to standard output and contain only numeric characters.

---
Task Requirements:

- Create a Bash script named count_procs.sh in the working directory.
- Use standard Linux tools such as ps or pgrep to list running processes.
- Count the number of running processes while avoiding header lines in command output.
- Print only the final numeric count and no additional text or formatting.
- Ensure the script runs reliably even if processes start or stop during execution.

---
Constraints:

- Do not print labels, explanations, or additional text.
- Do not prompt for user input or read from files.
- Do not hardcode a process count.
- Validation is performed by executing the script locally and inspecting its output.

