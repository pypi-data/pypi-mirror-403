#!/usr/bin/env python3
import os
import yaml
import sys

def validate():
    # --- Directory structure ---
    if not os.path.isdir("mychart"):
        return False, "Directory 'mychart' missing."

    chart_path = "mychart/Chart.yaml"
    if not os.path.exists(chart_path):
        return False, "Chart.yaml missing in mychart/."

    tmpl_path = "mychart/templates/deployment.yaml"
    if not os.path.exists(tmpl_path):
        return False, "deployment.yaml missing in mychart/templates/."

    # --- Validate Chart.yaml ---
    try:
        with open(chart_path) as f:
            chart = yaml.safe_load(f)
    except Exception as e:
        return False, f"Invalid YAML in Chart.yaml: {e}"

    if chart.get("apiVersion") != "v2":
        return False, "Chart.yaml must contain apiVersion: v2."

    if chart.get("name") != "mychart":
        return False, "Chart.yaml must contain name: mychart."

    if chart.get("version") != "0.1.0":
        return False, "Chart.yaml must contain version: 0.1.0."

    # --- Validate deployment.yaml ---
    try:
        with open(tmpl_path) as f:
            dep = yaml.safe_load(f)
    except Exception as e:
        return False, f"Invalid YAML in deployment.yaml: {e}"

    if dep.get("kind") != "Deployment":
        return False, "deployment.yaml must define kind: Deployment."

    if dep.get("metadata", {}).get("name") != "mychart-deploy":
        return False, (
            "deployment.yaml metadata.name must be mychart-deploy."
        )

    return True, "Basic Helm chart structure and content are correct."

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
