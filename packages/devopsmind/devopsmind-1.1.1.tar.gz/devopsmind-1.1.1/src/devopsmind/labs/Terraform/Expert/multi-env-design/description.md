# Design multi-environment Terraform configuration

Objective:

Design a Terraform configuration that supports multiple deployment environments
using a single codebase without duplicating resource definitions.

This lab evaluates expert-level infrastructure design thinking,
focusing on abstraction, reuse, and environment-driven behavior rather than
copy-paste configuration patterns.

---
Requirements:

- Terraform configuration must be written using standard HCL syntax
- The design must support at least two environments (for example: dev and prod)
- Environment-specific behavior must be controlled through variables and locals
- The solution must be static and file-based only
- No real infrastructure provisioning is required

---
Task Requirements:

- Create a variables.tf file defining an environment selector variable
- Create a locals.tf file that derives environment-specific behavior using conditionals
- Create a main.tf file that:
  - Defines a single resource block
  - Uses local values to control resource behavior
  - Avoids environment-specific logic inside the resource itself
- Ensure the configuration changes behavior based only on variable values

---
Constraints:

- Do NOT duplicate resource blocks for different environments
- Do NOT hardcode environment names or logic inside resource blocks
- Do NOT use multiple Terraform configurations per environment
- Do NOT run terraform init, plan, or apply
- Validation is static and file-based only

