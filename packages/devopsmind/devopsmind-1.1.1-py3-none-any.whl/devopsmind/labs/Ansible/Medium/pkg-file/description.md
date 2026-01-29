# Install Package and Create a File

Objective:

Demonstrate the ability to use an Ansible playbook to manage both a package
and a file in a declarative, idempotent manner.

---
Task Requirements:

Create or modify a file named: `playbook.yml`

The playbook must perform **two tasks**:

1. Ensure a package named `tree` is installed.
2. Ensure a file exists at `/tmp/info.txt` with the exact content: 

You may use appropriate Ansible modules for:
- Package management
- File or content management

---
Constraints:
- The playbook must be valid YAML
- Do not rely on roles or includes
- Do not assume the playbook is executed
- Validation is based on structure and intent, not actual system changes
