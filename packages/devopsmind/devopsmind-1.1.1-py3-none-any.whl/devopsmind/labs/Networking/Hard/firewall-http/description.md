# Set up firewall and test HTTP access

Objective:

- Analyze firewall configuration output to verify correct traffic filtering.
- Understand how firewall rules enforce access control for network services.
- Practice validating security posture without modifying live systems.

---
Requirements:

- Firewall status output files are provided in the working directory.
- The solution must be implemented as a shell script named analyze_firewall.sh.
- The script must work fully offline and read only local files.

---
Task Requirements:

- Read the provided firewall status output files.
- Verify that inbound traffic on port 80 is allowed.
- Verify that inbound traffic on all other ports is denied.
- Determine whether the firewall is enforcing an HTTP-only access policy.
- Print exactly the following output if the configuration is correct:
- Firewall correctly allows HTTP only

---
Constraints:

- Do not modify the firewall configuration files.
- Do not perform live firewall changes.
- Do not access the network.
- Validation is performed by executing the script and inspecting its output.

