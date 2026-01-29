# EC2 Resource Using Variables and Outputs

Objective:

Demonstrate how Terraform variables and outputs are used to create
configurable and reusable infrastructure.

This lab focuses on parameterizing an EC2 resource and exposing
important resource information through outputs.

---
Requirements:

- Basic understanding of Terraform configuration files
- Familiarity with variables and outputs
- No AWS credentials or execution required

---
Task Requirements:

Implement the following Terraform files:

1. variables.tf 

Define two variables -

- instance_type (string)
- ami (string)

2. main.tf -

Create an EC2 resource -

- Resource type: aws_instance
- Resource name: dev
- instance_type must reference var.instance_type
- ami must reference var.ami

Hardcoded values are NOT allowed.

3. outputs.tf 

Define an output -

- Output name: instance_id
- Value must reference aws_instance.dev.id

---
Constraints:

- Do NOT hardcode AMI or instance type values
- Do NOT run terraform init or apply
- Validation is static and file-based only
