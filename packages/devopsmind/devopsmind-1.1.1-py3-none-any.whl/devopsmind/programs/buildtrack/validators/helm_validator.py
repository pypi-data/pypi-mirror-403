from pathlib import Path

def validate_helm_files(path: Path):
    results = []
    chart = path / "Chart.yaml"

    if not chart.exists():
        results.append({
            "level": "improve",
            "symbol": "⚠️",
            "message": "Chart.yaml is missing",
            "why": "Helm charts require a chart definition.",
            "suggestion": "Add a Chart.yaml file.",
        })
    else:
        results.append({
            "level": "ok",
            "symbol": "✅",
            "message": "Helm chart definition found",
        })

    return results
