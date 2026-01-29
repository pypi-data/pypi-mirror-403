# Create User and Ensure Directory Exists (Idempotent)

Objective:

Demonstrate hard-level understanding of idempotent Ansible design by
managing both system users and filesystem state safely and predictably.

---
Task Requirements:

Create a file named: `playbook.yml`

The playbook must ensure:

1. A system user named `deploy` exists.
2. A directory exists at `/opt/deploy` with:
   - Ownership set to `deploy`
   - Permissions set to `0755`

Use appropriate Ansible modules to manage user and directory state.

---
Constraints:

- Do not assume the playbook is executed
- Do not rely on roles or includes
- Do not perform non-idempotent actions
- Validation is based on structure and declared intent
