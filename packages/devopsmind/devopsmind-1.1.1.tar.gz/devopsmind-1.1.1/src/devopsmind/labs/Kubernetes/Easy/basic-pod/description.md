# Create a Basic Pod

Objective:

Demonstrate understanding of the basic structure of a Kubernetes Pod manifest
and how a container is defined within it.

---
Requirements:

- The lab must be completed using a Kubernetes YAML manifest.
- The manifest must describe a single Pod.
- The manifest must be valid YAML.

---
Task Requirements:

- Create a file named pod.yaml.
- The manifest must specify:
  - apiVersion set to v1
  - kind set to Pod
  - A Pod name defined in metadata
- The Pod must define exactly one container.
- The container must specify a name and image.

---
Constraints:

- Do not use higher-level controllers (Deployment, ReplicaSet, Job).
- Do not reference external configuration or manifests.
- No Kubernetes cluster access is required or expected.
- Validation is static and file-based only.
