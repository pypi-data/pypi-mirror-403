# src/devopsmind/handlers/project/registry.py

from pathlib import Path
import yaml

from devopsmind.handlers.id_normalizer import canonical_id

# Same paths as list.py (single source of truth)
TIERS_DIR = Path.home() / ".devopsmind" / "tiers"


def _load_yaml(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception:
        return {}


def list_owned_project_ids() -> list[str]:
    """
    Headless project ID registry.
    - Reads tier YAMLs
    - Returns canonical project IDs
    - NO UI
    - NO Rich
    - SAFE for autocomplete
    """

    if not TIERS_DIR.exists():
        return []

    project_ids: set[str] = set()

    for tier_file in TIERS_DIR.glob("*.yaml"):
        tier = _load_yaml(tier_file)

        for pid in tier.get("project_ids", []):
            project_ids.add(canonical_id(pid))

    return sorted(project_ids)
