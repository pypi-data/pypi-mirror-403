# AWS Highly Available Web Architecture Requirements

The architecture must include:

- A public entry point for users
- A load balancing layer spanning multiple Availability Zones
- A compute layer deployed across multiple Availability Zones
- A storage service that is highly durable

Common AWS services used in this pattern include:
- Application Load Balancer
- EC2 in multiple AZs
- Auto Scaling Group
- S3
- VPC

The design should reflect real production AWS usage.
