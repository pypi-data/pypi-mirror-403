# Define Jenkins CI Governance Policy

Objective:

Define a Jenkins CI governance policy that addresses real failure scenarios,
organizational constraints, and systemic risk in a production environment.

This lab evaluates master-level engineering judgment by focusing on
policy design rather than tooling, emphasizing clarity, enforceability,
and balance between safety and delivery velocity.

---
Requirements:

- The solution must be expressed as a written CI governance policy
- The policy must be based only on the provided incident evidence and constraints
- The policy must apply to Jenkins CI pipelines and shared components
- Analysis and reasoning must be performed offline
- No pipeline execution or tooling configuration is required

---
Task Requirements:

- Review the provided incident summary describing CI failures
- Review the existing CI standards and governance constraints
- Create or update the ci-policy.md file to define:
  - The scope of the governance policy
  - At least three explicit governance rules
  - A clear justification for each rule
- Ensure the policy addresses ownership, review, and risk reduction
- Write the policy in clear language understandable by engineers at all levels

---
Constraints:

- Do NOT propose CI tools, plugins, or automation mechanisms
- Do NOT describe implementation details or enforcement systems
- Do NOT modify the provided incident or standards files
- Do NOT invent external context beyond the provided materials
- Focus exclusively on policy, standards, and engineering judgment

