from pathlib import Path

def validate():
    """
    Validation rules:
    - Jenkinsfile must exist in lab root
    - Must define a declarative pipeline
    - Must define stages block
    - Required stages must exist: Checkout, Build, Test
    - Each required stage must contain a steps block
    """

    jf_path = Path("Jenkinsfile")

    # 1. Jenkinsfile existence
    if not jf_path.exists():
        return False, "Jenkinsfile not found in lab root"

    jf = jf_path.read_text()

    required_stages = ["Checkout", "Build", "Test"]

    # 2. Basic declarative structure
    if "pipeline {" not in jf:
        return False, "Missing declarative pipeline block"

    if "stages {" not in jf:
        return False, "Missing stages block"

    # 3. Required stages and steps
    for stage in required_stages:
        if f"stage('{stage}')" in jf:
            stage_token = f"stage('{stage}')"
        elif f'stage("{stage}")' in jf:
            stage_token = f'stage("{stage}")'
        else:
            return False, f"Missing required stage: {stage}"

        stage_block = jf.split(stage_token, 1)[1]

        if "steps {" not in stage_block:
            return False, f"Stage '{stage}' must contain a steps block"

    return True, "Pipeline structure is valid"
