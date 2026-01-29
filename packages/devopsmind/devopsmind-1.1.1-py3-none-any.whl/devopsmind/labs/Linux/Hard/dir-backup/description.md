# Directory Backup Script

Objective:

Create a Bash script that performs a reliable, reproducible backup
of a directory using standard Linux archiving tools.

This lab focuses on scripting correctness, idempotency,
and archive structure verification.

---
Task Requirements:

Implement a script named backup.sh that creates a compressed
backup of a directory named data in the current working directory.

The script must:

- Produce a file named backup.tar.gz
- Include the data directory and its contents
- Preserve the internal directory structure
- Replace any existing backup archive when re-run

---
Constraints:

- Use tar with gzip compression
- Do NOT append to existing archives
- Do NOT rename the source directory
- Work fully offline and locally
- The validator will verify archive structure only

