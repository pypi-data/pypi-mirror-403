# Use locals and modules correctly

Objective:

Design a modular Terraform configuration that uses locals and reusable
modules to compose infrastructure cleanly and consistently.

This lab focuses on structuring Terraform code for long-term
maintainability, reuse, and professional-grade infrastructure design.

---
Requirements:

- Terraform configuration must be written in valid HCL
- The solution must use locals to define shared configuration
- A reusable module must be used to define infrastructure resources
- The configuration must be static and file-based only
- No real infrastructure provisioning is required

---
Task Requirements:

- Create a locals.tf file that defines:
  - An environment identifier
  - A shared tags map derived from locals
- Create a main.tf file that:
  - Declares a module
  - Passes local values into the module
- Create a module directory containing:
  - A variable definition for incoming values
  - A resource that consumes the passed-in locals
- Ensure configuration flows from locals into modules and then into resources

---
Constraints:

- Do NOT hardcode tag values inside resource blocks
- Do NOT duplicate configuration between root and module
- Do NOT run terraform init, plan, or apply
- Do NOT define resources directly in the root module
- Validation is static and file-based only

