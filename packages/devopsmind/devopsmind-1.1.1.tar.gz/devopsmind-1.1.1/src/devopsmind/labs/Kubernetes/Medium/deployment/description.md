# Create a Deployment with 3 replicas

Objective:

Demonstrate the ability to define a Kubernetes Deployment
that manages multiple replicas of an application using
a declarative YAML manifest.

This lab focuses on understanding how Deployments
control replica count and container configuration.

---
Task Requirements:

Create a file named deployment.yaml that defines a
Kubernetes Deployment with the following properties:

- apiVersion: apps/v1
- kind: Deployment
- metadata.name: web-deploy
- spec.replicas: 3

The Pod template must define:

- A single container
- Container name: web
- Container image: nginx:1.21

---
Constraints:

- Do NOT deploy the manifest to a cluster
- Do NOT use higher-level controllers
- Do NOT include additional containers
- Validation is static and file-based only

