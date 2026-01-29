# Conditionally render resources using Helm values

Objective:

Demonstrate expert-level Helm templating by conditionally rendering
Kubernetes resources based on chart values.

This lab evaluates whether conditional logic is applied correctly
and whether rendered resources remain dynamic and reusable.

---
Requirements:

- The solution must be implemented as a Helm chart.
- Chart configuration must be driven by values.
- Templates must remain dynamic and environment-aware.

---
Task Requirements:

Create or modify a Helm chart named mychart.

The chart must include:

- A values file that defines a configuration flag named config.enabled
- A message value under config.message
- A ConfigMap template that is rendered only when config.enabled is true
- The ConfigMap must reference the configured message value
- The ConfigMap name must be derived from the chart name

---
Constraints:

- Do NOT hardcode configuration values
- Do NOT render the resource unconditionally
- Do NOT run Helm or deploy resources
- Validation is static and file-based only

