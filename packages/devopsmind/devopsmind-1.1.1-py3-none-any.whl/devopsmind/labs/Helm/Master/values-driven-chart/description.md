# Design a values-driven Helm chart

Objective:

Design a Helm chart whose deployment behavior is fully controlled through
values.yaml rather than hardcoded template logic.

This lab evaluates master-level Helm chart design, focusing on
configuration-driven behavior, reuse across environments, and long-term
maintainability of chart templates.

---
Requirements:

- The solution must be implemented as a Helm chart
- The chart must include a values.yaml file
- The chart must include a Deployment template
- Deployment behavior must be controlled exclusively through values and chart metadata
- Validation is static and file-based only

---
Task Requirements:

- Define a replicaCount value in values.yaml
- Define image configuration in values.yaml, including:
  - image.repository
  - image.tag
- Configure the Deployment template to:
  - Set spec.replicas using .Values.replicaCount
  - Set the container image using values from image.repository and image.tag
  - Derive the Deployment name from chart metadata
- Ensure all behavior changes can be achieved by modifying values.yaml only

---
Constraints:

- Do NOT hardcode replica counts in templates
- Do NOT hardcode image names or tags in templates
- Do NOT modify templates to change environment behavior
- Do NOT run Helm commands or render templates
- Validation relies solely on static inspection of local files

