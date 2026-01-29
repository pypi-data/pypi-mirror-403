from pathlib import Path

def validate():
    """
    Medium-level validation:
    - Jenkinsfile must define a declarative pipeline
    - Required stages must exist: Checkout, Build, Test
    - Steps must be present
    - Failure notes must reference test failure evidence
    """

    # --- File existence ---
    jf_path = Path("Jenkinsfile")
    notes_path = Path("failure-notes.md")

    if not jf_path.exists():
        return False, "Jenkinsfile not found"

    if not notes_path.exists():
        return False, "failure-notes.md not found"

    jenkinsfile = jf_path.read_text()
    notes = notes_path.read_text()

    required_stages = ["Checkout", "Build", "Test"]

    # --- Jenkinsfile structure ---
    if "pipeline {" not in jenkinsfile:
        return False, "Missing declarative pipeline block"

    if "stages {" not in jenkinsfile:
        return False, "Missing stages block"

    for stage in required_stages:
        if (
            f"stage('{stage}')" not in jenkinsfile and
            f'stage("{stage}")' not in jenkinsfile
        ):
            return False, f"Missing required stage: {stage}"

    if "steps {" not in jenkinsfile:
        return False, "Pipeline stages must contain steps"

    # --- Failure notes validation ---
    if "Test" not in notes:
        return False, "Failure notes must mention the Test stage"

    if "AssertionError" not in notes:
        return False, "Failure notes must reference AssertionError from test log"

    return True, "Failure-handling pipeline design is valid"
