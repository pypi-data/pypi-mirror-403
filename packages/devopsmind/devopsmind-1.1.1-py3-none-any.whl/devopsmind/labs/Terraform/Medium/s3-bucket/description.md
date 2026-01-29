# Create an AWS S3 Bucket Using Terraform

Objective

Demonstrate the ability to define a Terraform resource that provisions
cloud infrastructure declaratively using infrastructure-as-code principles.

This lab focuses on Terraform resource syntax and configuration
structure, not real cloud deployment.

---
Requirements:

- Terraform configuration must be written in HCL
- Validation is static and file-based only
- No Terraform commands are required to be executed

---
Task Requirements:

Create or update a file named `main.tf` to include:

- A resource block of type `aws_s3_bucket`
- Resource name must be `devops_bucket`
- The bucket attribute must be set to:
  - `devopsmind-bucket`

The provider block from the Easy Terraform lab may remain unchanged.

---
Constraints:

- Do NOT apply or plan Terraform
- Do NOT define additional resources
- Do NOT change the expected bucket name
- Do NOT access AWS or the network
- Validation checks file content only
