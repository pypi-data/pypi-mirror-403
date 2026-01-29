# Build Robust Data Processing Pipeline

Objective:

- Build a Bash script that processes structured numeric input using command pipelines.
- Understand how data flows through multiple commands connected by pipes.
- Learn how error handling and exit codes affect the reliability of shell automation.

---
Requirements:

- A file named numbers.txt is provided in the working directory.
- The solution must be implemented as a Bash script named process_numbers.sh.
- The script must be executable and runnable from the command line.

---
Task Requirements:

- Create a script named process_numbers.sh.
- Read numeric values from numbers.txt.
- Filter the input to include only even numbers.
- Calculate the sum of the filtered values.
- Print only the final numeric sum to standard output.
- Exit with a non-zero status if numbers.txt is missing or unreadable.

---
Constraints:

- Do not modify the numbers.txt file.
- Do not print explanatory text or additional output.
- Do not use non-standard or external tools.
- Validation is performed by executing the script locally and inspecting its output and exit code.

