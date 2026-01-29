# Define a Basic Argo CD Application

Objective:

Demonstrate understanding of the basic structure of an Argo CD Application
by completing a valid declarative configuration.

In GitOps-driven environments, Applications are defined in version control
and reviewed before being applied to any cluster.

---
Task Requirements:

Edit the provided file - `application.yaml`

The Application definition must:
1. Define application metadata
2. Specify a Git source repository
3. Specify a destination cluster and namespace
4. Enable automated synchronization

You may refer to:
- `configs/requirements.md` for required fields

---
Constraints:
- Do NOT deploy to a Kubernetes cluster
- Do NOT reference real credentials
- Do NOT add advanced sync options
- Validation is static and file-based only
