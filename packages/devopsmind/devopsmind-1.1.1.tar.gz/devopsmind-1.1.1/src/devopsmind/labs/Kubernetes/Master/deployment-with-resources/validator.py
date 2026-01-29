#!/usr/bin/env python3
import os
import yaml

def validate():
    path = "deployment.yaml"

    if not os.path.exists(path):
        message = "deployment.yaml missing."
        return False, message

    try:
        d = yaml.safe_load(open(path))
    except Exception as e:
        message = f"Invalid YAML: {e}"
        return False, message

    if d.get("kind") != "Deployment":
        message = "Must define a Deployment."
        return False, message

    if d.get("metadata", {}).get("name") != "resource-deploy":
        message = "Deployment name must be resource-deploy."
        return False, message

    if d.get("spec", {}).get("replicas") != 2:
        message = "replicas must be 2."
        return False, message

    containers = (
        d.get("spec", {})
         .get("template", {})
         .get("spec", {})
         .get("containers", [])
    )

    if not containers:
        message = "Deployment must define containers."
        return False, message

    c = containers[0]

    if c.get("name") != "app":
        message = "Container name must be app."
        return False, message

    if c.get("image") != "nginx:alpine":
        message = "Container image must be nginx:alpine."
        return False, message

    resources = c.get("resources", {})
    req = resources.get("requests", {})
    lim = resources.get("limits", {})

    if req.get("cpu") != "100m" or req.get("memory") != "128Mi":
        message = "CPU/memory requests incorrect."
        return False, message

    if lim.get("cpu") != "500m" or lim.get("memory") != "256Mi":
        message = "CPU/memory limits incorrect."
        return False, message

    message = "Kubernetes Master lab passed!"
    return True, message

if __name__ == "__main__":
    ok, message = validate()
    print(message)
