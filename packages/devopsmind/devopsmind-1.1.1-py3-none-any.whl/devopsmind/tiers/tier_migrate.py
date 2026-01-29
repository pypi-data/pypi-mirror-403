from pathlib import Path
import yaml

FOUNDATION_TIER_FILE = "foundation_core.yaml"


def migrate_foundation_core_visibility():
    """
    Ensure ~/.devopsmind/tiers/foundation_core.yaml exists.

    PURPOSE:
    - Foundation Core is always live and bundled
    - User copy is ONLY a marker for ownership / UI
    - Visibility is resolved from bundled YAML, not user file

    HARD RULES:
    - Create marker if missing
    - NEVER overwrite
    - NEVER append or remove labs
    - NEVER block execution
    - Fully offline-safe
    """

    try:
        bundled = (
            Path(__file__).parent
            / "foundation_core"
            / FOUNDATION_TIER_FILE
        )

        if not bundled.exists():
            return

        user_dir = Path.home() / ".devopsmind" / "tiers"
        user_dir.mkdir(parents=True, exist_ok=True)

        user_marker = user_dir / FOUNDATION_TIER_FILE

        # -------------------------------------------------
        # Create marker ONCE
        # -------------------------------------------------
        if not user_marker.exists():
            data = yaml.safe_load(bundled.read_text()) or {}

            marker = {
                "tier": "foundation_core",
                "name": data.get("name", "Foundation Core"),
            }

            user_marker.write_text(
                yaml.safe_dump(marker, sort_keys=False)
            )

    except Exception:
        # Migration must NEVER break DevOpsMind
        pass
