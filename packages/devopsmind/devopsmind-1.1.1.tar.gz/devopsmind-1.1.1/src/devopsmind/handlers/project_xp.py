from pathlib import Path
import yaml


def load_project_xp(project_dir: Path) -> int:
    """
    Load XP for a project capstone.

    HARD RULES:
    - project.yaml must exist
    - XP is granted ONLY on completion
    - Missing / invalid XP → 0
    - Project XP is separate from lab XP
    """
    try:
        data = yaml.safe_load((project_dir / "project.yaml").read_text()) or {}
        return int(data.get("project_xp", data.get("xp", 0)))
    except Exception:
        return 0
