# Design an Ansible Role Using Variables

Objective:

Demonstrate master-level understanding of Ansible role design by
creating a reusable role that separates configuration from execution
logic using variables.

---
Task Requirements:

Create an Ansible role named `web` under the `roles/` directory.

The role must -

- Define configurable values using role defaults
- Reference those values inside role tasks
- Follow standard Ansible role directory structure

The role should demonstrate how configuration can be adjusted without
modifying task logic.

---
Constraints:
- Do not include a full playbook
- Do not execute Ansible
- Do not hardcode configuration values inside tasks
- Validation is static and file-based only
