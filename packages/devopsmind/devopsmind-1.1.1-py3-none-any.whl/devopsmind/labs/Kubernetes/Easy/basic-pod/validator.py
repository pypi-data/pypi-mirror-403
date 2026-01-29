#!/usr/bin/env python3
import os
import yaml

def validate():
    if not os.path.exists("pod.yaml"):
        message = "pod.yaml missing."
        return False, message

    try:
        with open("pod.yaml") as f:
            pod = yaml.safe_load(f)
    except Exception as e:
        message = f"Invalid YAML: {e}"
        return False, message

    if not isinstance(pod, dict):
        message = "Pod manifest must be a YAML mapping."
        return False, message

    if pod.get("apiVersion") != "v1":
        message = "apiVersion must be v1."
        return False, message

    if pod.get("kind") != "Pod":
        message = "kind must be Pod."
        return False, message

    meta = pod.get("metadata", {})
    if meta.get("name") != "hello-pod":
        message = "Pod name must be hello-pod."
        return False, message

    spec = pod.get("spec", {})
    containers = spec.get("containers", [])

    if not isinstance(containers, list) or len(containers) != 1:
        message = "Pod must have exactly one container."
        return False, message

    c = containers[0]
    if c.get("name") != "web":
        message = "Container name must be web."
        return False, message

    if c.get("image") != "nginx":
        message = "Container image must be nginx."
        return False, message

    message = "Basic Pod manifest is correct!"
    return True, message

