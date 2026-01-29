# Create main.tf with a provider block

Objective:

Introduce the foundational Terraform concept of providers by
authoring a minimal configuration that defines a cloud provider.

This lab focuses on Terraform syntax and structure,
not real infrastructure deployment.

---
Requirements:

- Terraform configuration must be written in HCL
- Validation is static and file-based only
- No Terraform commands need to be executed

---
Task Requirements:

Create a file named main.tf that defines:

- A provider block named aws
- A region set to "us-east-1"

Example structure:

provider "aws" {
  region = "us-east-1"
}

---
Constraints:

- Do NOT define resources
- Do NOT initialize or apply Terraform
- Do NOT include additional provider configuration
- Validation is based on file content only

