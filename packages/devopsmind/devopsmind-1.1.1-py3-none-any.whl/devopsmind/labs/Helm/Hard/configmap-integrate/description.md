# Deployment must mount ConfigMap created via template

Objective:

Integrate a ConfigMap created via a Helm template into a Kubernetes Deployment
and ensure it is mounted correctly at runtime.

This lab evaluates understanding of how Helm templates coordinate
multiple Kubernetes resources through shared configuration.

---
Requirements:

- The solution must be implemented as a Helm chart.
- Configuration values must be defined in values.yaml.
- The chart must include both a ConfigMap and a Deployment template.

---
Task Requirements:

Complete the following Helm chart integration:

- Define a configuration value under config.message in values.yaml
- Create a ConfigMap template that uses the configured message value
- Ensure the ConfigMap name is derived from the chart name
- Modify the Deployment template to reference the ConfigMap as a volume
- Mount the ConfigMap into the container filesystem

The Deployment must correctly reference the templated ConfigMap using
volumes and volumeMounts.

---
Constraints:

- Do NOT hardcode configuration values
- Do NOT embed configuration directly into the Deployment
- Do NOT deploy or run Helm
- Validation is static and file-based only

