# Design a secure Pod using securityContext

Objective:

- Design a Kubernetes Pod that applies secure runtime settings using securityContext.
- Understand how Kubernetes enforces least-privilege execution for containers.
- Learn how runtime user identity, privilege escalation, and filesystem access affect Pod security.
- Focus on static security configuration rather than runtime enforcement or cluster interaction.

---
Requirements:

- The solution must be implemented using a Kubernetes YAML manifest file named pod.yaml.
- The manifest must define a single Pod resource using apiVersion v1 and kind Pod.
- The Pod must run a container using the nginx:alpine image.
- All security requirements must be enforced using securityContext at the Pod or container level.
- The manifest must be valid YAML and suitable for static inspection.

---
Task Requirements:

- Create a pod.yaml file that defines a Pod named secure-pod.
- Configure the Pod or container to run as a non-root user by setting runAsNonRoot to true.
- Explicitly set runAsUser to 1000 to avoid implicit runtime defaults.
- Disable privilege escalation by setting allowPrivilegeEscalation to false.
- Configure the container filesystem to be read-only by enabling readOnlyRootFilesystem.
- Ensure all security-related fields are defined using securityContext rather than external mechanisms.

---
Constraints:

- Do not deploy the Pod to a Kubernetes cluster.
- Do not execute kubectl or any other Kubernetes commands.
- Do not rely on external security tools, admission controllers, or policies.
- Validation is performed using static file inspection only and focuses solely on manifest correctness.

