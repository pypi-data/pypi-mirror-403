#!/usr/bin/env python3
from pathlib import Path
import sys

def validate():
    """
    Easy-level Argo CD Application validation.

    - Structure-focused
    - Beginner-friendly
    - Offline-safe
    """

    app_path = Path("application.yaml")
    requirements_path = Path("configs/requirements.md")

    if not requirements_path.exists():
        return False, (
            "Missing provided file: configs/requirements.md\n"
            "This reference file must be present."
        )

    if not app_path.exists():
        return False, (
            "application.yaml not found.\n"
            "You must define the Argo CD Application in this file."
        )

    try:
        content = app_path.read_text(encoding="utf-8")
    except Exception:
        return False, "Unable to read application.yaml."

    # Required top-level fields
    required_strings = [
        "apiVersion: argoproj.io/v1alpha1",
        "kind: Application",
        "metadata:",
        "name:",
        "spec:",
        "source:",
        "repoURL:",
        "path:",
        "destination:",
        "server:",
        "namespace:",
        "syncPolicy:",
        "automated"
    ]

    for field in required_strings:
        if field not in content:
            return False, (
                f"Missing required field or section: {field}\n"
                "Review configs/requirements.md for required structure."
            )

    # Ensure metadata.name is not empty
    for line in content.splitlines():
        if line.strip().startswith("name:"):
            if not line.split("name:", 1)[1].strip():
                return False, (
                    "metadata.name is empty.\n"
                    "Provide a non-empty application name."
                )

    return True, (
        "Argo CD Application definition is valid.\n"
        "All required fields and files are present."
    )

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
