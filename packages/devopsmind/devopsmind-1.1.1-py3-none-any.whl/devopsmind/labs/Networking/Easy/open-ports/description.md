# Write a script to test open ports

Objective:

- Learn how to test basic network connectivity by checking open ports.
- Understand how ports map to services running on a system.
- Practice writing a simple script that verifies service availability.

---
Requirements:

- The solution must be implemented as a script named check_ports.sh.
- The script must run on the local system without requiring network access.
- The script must check ports on localhost only.

---
Task Requirements:

- Create a script named check_ports.sh in the working directory.
- Test whether the following ports are open on localhost:
  - Port 22
  - Port 80
  - Port 443
- For each port tested, print a line indicating whether the port is open or closed.
- Ensure the script runs without errors and produces readable output.

---
Constraints:

- Do not scan remote hosts.
- Do not use advanced scanning tools or libraries.
- Do not require elevated privileges.
- Validation is performed by executing the script and inspecting its output.

