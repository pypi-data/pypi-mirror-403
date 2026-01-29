#!/usr/bin/env python3
import os
import yaml

def validate():
    if not os.path.exists("deployment.yaml"):
        message = "deployment.yaml missing."
        return False, message

    try:
        with open("deployment.yaml") as f:
            d = yaml.safe_load(f)
    except Exception as e:
        message = f"Invalid YAML: {e}"
        return False, message

    if d.get("apiVersion") != "apps/v1":
        message = "apiVersion must be apps/v1."
        return False, message

    if d.get("kind") != "Deployment":
        message = "Kind must be Deployment."
        return False, message

    if d.get("metadata", {}).get("name") != "web-deploy":
        message = "metadata.name must be web-deploy."
        return False, message

    spec = d.get("spec", {})
    if spec.get("replicas") != 3:
        message = "replicas must be 3."
        return False, message

    tmpl = spec.get("template", {})
    containers = tmpl.get("spec", {}).get("containers", [])
    if not containers:
        message = "Deployment must define containers."
        return False, message

    c = containers[0]
    if c.get("name") != "web":
        message = "Container name must be web."
        return False, message

    if c.get("image") != "nginx:1.21":
        message = "Container image must be nginx:1.21."
        return False, message

    message = "Deployment manifest is correct!"
    return True, message
