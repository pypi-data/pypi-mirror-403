# Template must use values.yaml variable

Objective:

Demonstrate how Helm values.yaml is used to parameterize chart templates,
allowing the same chart to be reused across environments without modifying
template files.

This lab focuses on replacing hardcoded values in templates with
dynamic values provided through values.yaml.

---
Requirements:

- A Helm chart directory named mychart must exist
- The chart must include a values.yaml file
- The chart must include a templates/deployment.yaml file
- Configuration must be expressed using Helm templating syntax
- Validation is static and file-based only

---
Task Requirements:

- Define an image field in mychart/values.yaml
- Set the image value to nginx:alpine
- Modify templates/deployment.yaml to:
  - Use {{ .Values.image }} for the container image
  - Generate the Deployment name using {{ .Chart.Name }}-deploy
- Ensure no hardcoded image values exist in the template

---
Constraints:

- Do NOT hardcode container image values in templates
- Do NOT render or install the Helm chart
- Do NOT execute Helm commands
- Only static inspection of files is performed
- Validation must pass using local file content only

