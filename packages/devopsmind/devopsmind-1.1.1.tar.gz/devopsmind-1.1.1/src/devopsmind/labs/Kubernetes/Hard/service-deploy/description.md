# Expose Deployment with a Service

Objective:

- Design Kubernetes resources that expose an application Deployment internally using a Service.
- Understand how Kubernetes networking works through labels and selectors rather than fixed IPs.
- Learn how multiple resource definitions interact to provide stable service discovery inside a cluster.
- Focus on reasoning about configuration and relationships between resources instead of runtime execution.

---
Requirements:

- The solution must consist of two Kubernetes YAML manifest files named deployment.yaml and service.yaml.
- The Deployment manifest must define an application workload that runs multiple replicas.
- The Service manifest must expose the Pods created by the Deployment internally within the cluster.
- All manifests must be written in valid YAML and structured according to Kubernetes resource specifications.
- The files must be suitable for static inspection without requiring a running Kubernetes cluster.

---
Task Requirements:
- Create a deployment.yaml file that defines a Kubernetes Deployment named web-deploy.
- Configure the Deployment to manage exactly two replicas.
- Apply a label app=web to the Pod template metadata so that other resources can select the Pods.
- Define a single container in the Pod template with the name web.
- Configure the container to use the nginx:alpine image.
- Create a service.yaml file that defines a Kubernetes Service named web-service.
- Set the Service type to ClusterIP to ensure internal-only exposure.
- Configure the Service selector to match the app=web label defined in the Deployment.
- Expose port 80 on the Service and forward traffic to port 80 on the target container.
- Ensure label and selector consistency so that traffic is correctly routed from the Service to the Deployment Pods.

---
Constraints:

- Do not deploy the manifests to a Kubernetes cluster.
- Do not execute kubectl or any other Kubernetes commands.
- Do not expose the application externally using NodePort or LoadBalancer Service types.
- Do not define additional containers, resources, or configuration beyond what is required.
- Validation is performed using static file inspection only and depends on correct cross-file configuration.

