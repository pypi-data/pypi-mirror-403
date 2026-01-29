# Use conditionals and handlers correctly

Objective:

Demonstrate expert-level understanding of Ansible control flow by correctly
combining conditional task execution with handlers.

This lab evaluates whether handlers trigger only when appropriate
and whether conditional logic is applied correctly.

---
Requirements:

- The solution must be written as an Ansible playbook.
- The playbook must be valid YAML.
- The playbook must define at least one task and one handler.

---
Task Requirements:

Create a file named playbook.yml.

The playbook must demonstrate the following behaviors:

- A task that updates configuration
- The task executes conditionally using a when clause
- The task notifies a handler when it reports change
- A handler exists with the expected name
- The handler performs a debug-style action

---
Constraints:

- Do NOT run Ansible
- Do NOT perform real system changes
- Focus on control flow, not infrastructure
- Validation is static and file-based only
