from pathlib import Path
import yaml

def validate_gitops_files(path: Path):
    results = []
    yamls = list(path.glob("*.yml")) + list(path.glob("*.yaml"))

    if not yamls:
        results.append({
            "level": "improve",
            "symbol": "⚠️",
            "message": "No declarative GitOps manifests found",
            "why": "GitOps relies on desired state stored in version control.",
            "suggestion": "Add declarative YAML manifests that describe desired state.",
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
                "why": "Declarative manifests must be syntactically valid.",
                "suggestion": "Fix indentation or formatting.",
            })
            continue

        # Gentle declarative hint (non-blocking)
        if isinstance(data, dict) and "kind" not in data:
            results.append({
                "level": "info",
                "symbol": "ℹ️",
                "message": f"{y.name} does not declare a resource kind",
                "why": "Declarative delivery often describes specific resources.",
                "suggestion": "Consider clarifying what resource this manifest represents.",
            })

    results.append({
        "level": "ok",
        "symbol": "✅",
        "message": "Declarative GitOps manifests parsed successfully",
    })

    return results
