# Define a Deployment with resource requests and limits

Objective:

Demonstrate the ability to define a **production-ready Kubernetes Deployment**
by specifying appropriate CPU and memory requests and limits for containers.

This lab focuses on resource management decisions that affect
scheduling, stability, and cluster utilization.

---
Requirements:

- The solution must be expressed as a Kubernetes YAML manifest
- The manifest must define a Deployment
- Resource requests and limits must be specified for containers

---
Task Requirements:

Create a file named deployment.yaml that defines a Kubernetes Deployment
with the following properties:

Deployment configuration -
- apiVersion must be apps/v1
- kind must be Deployment
- metadata name must be resource-deploy
- replica count must be 2

Container configuration - 
- Container name must be app
- Container image must be nginx:alpine

Resource configuration - 
- CPU request: 100m
- Memory request: 128Mi
- CPU limit: 500m
- Memory limit: 256Mi

Resources must be defined under the container resources section.

---
Constraints:

- Do NOT deploy the manifest to a Kubernetes cluster
- Do NOT use kubectl or runtime inspection
- Do NOT add additional containers
- Validation is static and file-based only
