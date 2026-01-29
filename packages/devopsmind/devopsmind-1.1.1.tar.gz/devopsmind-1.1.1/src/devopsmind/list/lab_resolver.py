from pathlib import Path

LABS_ROOT = Path(__file__).resolve().parents[1] / "labs"


# -------------------------------------------------
# Core resolvers
# -------------------------------------------------
def find_lab_by_id(lab_id: str):
    """
    Find a LAB directory by its ID.

    HARD RULE:
    - Must contain lab.yaml
    - Must NOT be a project (project.yaml)
    """
    for path in LABS_ROOT.rglob(lab_id):
        if not path.is_dir():
            continue

        # Must be a lab
        if not (path / "lab.yaml").exists():
            continue

        # Must NOT be a project
        if (path / "project.yaml").exists():
            continue

        return path

    return None


def list_all_labs():
    """
    Return a list of all LAB IDs.

    HARD RULE:
    - lab.yaml defines labs
    - project.yaml explicitly excludes directories
    """
    labs = []

    for lab_yaml in LABS_ROOT.rglob("lab.yaml"):
        lab_dir = lab_yaml.parent

        # Exclude projects defensively
        if (lab_dir / "project.yaml").exists():
            continue

        labs.append(lab_dir.name)

    return sorted(labs)


# -------------------------------------------------
# Public API aliases (MANDATORY)
# -------------------------------------------------

# New preferred name
get_all_labs = list_all_labs

# Backward compatibility (temporary)
find_challenge_by_id = find_lab_by_id
list_all_challenges = list_all_labs
get_all_challenges = list_all_labs
