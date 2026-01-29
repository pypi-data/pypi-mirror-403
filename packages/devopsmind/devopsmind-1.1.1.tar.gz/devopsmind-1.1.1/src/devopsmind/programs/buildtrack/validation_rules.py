# src/devopsmind/programs/buildtrack/validation_rules.py

from pathlib import Path

from .validators.design_validator import validate_design_file
from .validators.docker_validator import validate_dockerfile
from .validators.shell_validator import validate_shell_scripts
from .validators.yaml_validator import validate_yaml_files
from .validators.helm_validator import validate_helm_files
from .validators.cicd_validator import validate_cicd_files
from .validators.gitops_validator import validate_gitops_files


# BuildTrack expected structure (existence only)
REQUIRED_FOLDERS = [
    "execution/linux",
    "execution/git",
    "execution/docker",
    "resilience/kubernetes",
    "resilience/helm",
    "delivery/cicd",
    "delivery/gitops",
]


def _scope_name(folder: str) -> str:
    """
    execution/linux -> Linux
    delivery/cicd   -> CICD
    """
    return folder.split("/")[-1].capitalize()


def _section_header(scope: str):
    """
    Emits a visual section header for the UI.
    """
    return {
        "level": "section",
        "symbol": "",
        "message": scope,
        "divider": True,
    }


def run_validation(workspace_root: str):
    """
    BuildTrack validation entrypoint.

    - Groups validation output by responsibility/tool
    - Validates DESIGN.md placeholder replacement
    - Validates tool-specific artifacts
    - Advisory only (does not block progress)
    """

    results = []
    root = Path(workspace_root)

    for folder in REQUIRED_FOLDERS:
        path = root / folder
        scope = _scope_name(folder)

        # --------------------------------------------------
        # Section header (always shown)
        # --------------------------------------------------
        results.append(_section_header(scope))

        # --------------------------------------------------
        # Structure validation
        # --------------------------------------------------
        if not path.exists():
            results.append({
                "level": "improve",
                "symbol": "⚠️",
                "message": f"Expected directory `{folder}` is missing",
                "why": "Each directory represents a design responsibility.",
                "suggestion": "Create the directory to capture design and declarative artifacts.",
            })
            continue

        # --------------------------------------------------
        # DESIGN.md validation (mandatory everywhere)
        # --------------------------------------------------
        results.extend(validate_design_file(path))

        # --------------------------------------------------
        # Tool-specific validation
        # --------------------------------------------------
        if folder.endswith("linux"):
            results.extend(validate_shell_scripts(path))

        elif folder.endswith("docker"):
            results.extend(validate_dockerfile(path))

        elif folder.endswith("kubernetes"):
            results.extend(validate_yaml_files(path))

        elif folder.endswith("helm"):
            results.extend(validate_helm_files(path))

        elif folder.endswith("cicd"):
            results.extend(validate_cicd_files(path))

        elif folder.endswith("gitops"):
            results.extend(validate_gitops_files(path))

        # git folder intentionally has DESIGN.md only

    return results
