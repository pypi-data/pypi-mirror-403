# Create a basic Helm chart structure

Objective:

Understand and create the minimal directory and file
structure required for a valid Helm chart.

---
Requirements:

A Helm chart directory must exist with chart metadata
and a Kubernetes Deployment template.

---
Task Requirements:

1. Create a Helm chart directory named mychart.
2. Create a chart metadata file at mychart/Chart.yaml.
3. Create a Deployment template at
   mychart/templates/deployment.yaml.
4. Chart.yaml must define apiVersion, name, and version.
5. deployment.yaml must define a Kubernetes Deployment
   with a metadata name.

---
Constraints:

Do NOT deploy the chart.
Do NOT use Helm CLI commands.
Do NOT add values.yaml or helper templates.
Focus only on structure and correctness.
Work fully offline using local files only.
