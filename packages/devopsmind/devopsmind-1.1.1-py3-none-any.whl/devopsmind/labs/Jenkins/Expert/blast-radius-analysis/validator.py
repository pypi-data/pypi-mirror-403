from pathlib import Path

def validate():
    """
    Expert-level Jenkins blast radius analysis validation.
    """

    # --- Required analysis output ---
    analysis_path = Path("impact-analysis.md")

    if not analysis_path.exists():
        message = (
            "Impact analysis file not found.\n"
            "The file `impact-analysis.md` must exist to perform validation."
        )
        return False, message

    # --- Required evidence directory ---
    manifests_dir = Path("manifests")
    if not manifests_dir.exists() or not manifests_dir.is_dir():
        message = (
            "CI manifests directory missing.\n"
            "A directory named 'manifests' must be present."
        )
        return False, message

    try:
        analysis = analysis_path.read_text()
    except Exception:
        message = (
            "Unable to read impact-analysis.md.\n"
            "Ensure the file exists and is readable."
        )
        return False, message

    required_sections = [
        "Shared Component",
        "Affected Pipelines",
        "Failure Propagation",
        "Blast Radius Reduction"
    ]

    for section in required_sections:
        if section not in analysis:
            message = (
                f"Missing required section: {section}.\n"
                "A complete blast radius analysis must follow the standard structure."
            )
            return False, message

    analysis_lower = analysis.lower()

    if "shared" not in analysis_lower:
        message = (
            "The analysis does not clearly identify a shared CI component.\n"
            "Blast radius analysis must demonstrate awareness of shared dependencies."
        )
        return False, message

    if "service-a" not in analysis_lower or "service-b" not in analysis_lower:
        message = (
            "The analysis does not include all pipelines impacted by the shared component.\n"
            "A complete blast radius analysis must explicitly cover every affected pipeline."
        )
        return False, message

    message = (
        "Blast radius analysis is complete and system-aware.\n"
        "Shared dependency impact and mitigation are clearly documented."
    )
    return True, message

