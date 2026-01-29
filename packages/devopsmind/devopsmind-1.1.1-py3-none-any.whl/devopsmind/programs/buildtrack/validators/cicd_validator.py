from pathlib import Path
import yaml

CI_FILES = [
    "Jenkinsfile",
    ".gitlab-ci.yml",
]

def validate_cicd_files(path: Path):
    results = []

    files = list(path.glob("*"))
    workflow_files = list(path.glob(".github/workflows/*.yml"))
    circle_files = list(path.glob(".circleci/config.yml"))

    candidates = files + workflow_files + circle_files

    if not candidates:
        results.append({
            "level": "improve",
            "symbol": "⚠️",
            "message": "No CI/CD configuration found",
            "why": "CI/CD files represent automated change validation.",
            "suggestion": "Add at least one CI/CD configuration file.",
        })
        return results

    parsed_any = False

    for f in candidates:
        if f.suffix in [".yml", ".yaml"]:
            try:
                yaml.safe_load(f.read_text())
                parsed_any = True
            except Exception:
                results.append({
                    "level": "improve",
                    "symbol": "⚠️",
                    "message": f"Invalid YAML syntax in {f.name}",
                    "why": "CI/CD configurations must be syntactically valid.",
                    "suggestion": "Fix indentation or formatting.",
                })
        else:
            # Jenkinsfile or other text-based pipelines
            parsed_any = True

    if parsed_any:
        results.append({
            "level": "ok",
            "symbol": "✅",
            "message": "CI/CD configuration files detected",
        })

    return results
