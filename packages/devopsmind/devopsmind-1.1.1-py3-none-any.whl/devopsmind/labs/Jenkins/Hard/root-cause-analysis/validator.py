from pathlib import Path

def validate():
    """
    Hard-level Jenkins RCA validation.
    Ensures structure, evidence-based reasoning, and CI-stage awareness.
    """

    rca_path = Path("rca.md")

    if not rca_path.exists():
        return False, (
            "RCA not started yet.\n"
            "The file `rca.md` must be completed before validation."
        )

    rca = rca_path.read_text()

    required_sections = [
        "Observed Failure",
        "Root Cause",
        "Contributing Factors",
        "Corrective Action"
    ]

    # --- Structural validation ---
    for section in required_sections:
        if section not in rca:
            return False, (
                f"Missing required section: {section}.\n"
                "A complete RCA must follow the standard incident analysis structure."
            )

    # --- Evidence-based validation ---
    if "NullPointerException" not in rca:
        return False, (
            "The RCA does not reference the actual exception that caused the failure.\n"
            "A valid root cause analysis must be grounded in the observed error."
        )

    if "Test" not in rca:
        return False, (
            "The RCA does not clearly identify the pipeline stage where the failure occurred.\n"
            "Incident analysis must specify the stage in which the failure was observed."
        )

    return True, (
        "Root Cause Analysis is complete and evidence-based.\n"
        "The failure has been correctly analyzed and documented."
    )
