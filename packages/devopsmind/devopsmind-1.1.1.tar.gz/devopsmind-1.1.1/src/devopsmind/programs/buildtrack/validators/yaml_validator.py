import yaml
from pathlib import Path

def validate_yaml_files(path: Path):
    results = []
    yamls = list(path.glob("*.yml")) + list(path.glob("*.yaml"))

    if not yamls:
        results.append({
            "level": "improve",
            "symbol": "⚠️",
            "message": "No YAML manifests found",
            "why": "Declarative files represent desired state.",
            "suggestion": "Add Kubernetes YAML manifests.",
        })
        return results

    for y in yamls:
        try:
            data = yaml.safe_load(y.read_text())
        except Exception:
            results.append({
                "level": "improve",
                "symbol": "⚠️",
                "message": f"Invalid YAML syntax in {y.name}",
                "why": "YAML must be syntactically correct to be declarative.",
                "suggestion": "Fix indentation or formatting.",
            })
            continue

        for key in ["apiVersion", "kind", "metadata", "spec"]:
            if key not in data:
                results.append({
                    "level": "info",
                    "symbol": "ℹ️",
                    "message": f"{y.name} is missing `{key}`",
                    "why": "Kubernetes resources usually define this field.",
                })

    results.append({
        "level": "ok",
        "symbol": "✅",
        "message": "YAML manifests parsed successfully",
    })

    return results
