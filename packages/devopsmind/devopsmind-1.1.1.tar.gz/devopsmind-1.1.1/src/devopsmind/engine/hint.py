from pathlib import Path
import yaml
from rich.text import Text
import os

from devopsmind.list.lab_resolver import find_lab_by_id

WORKSPACE_DIR = Path.home() / "workspace"
PLAY_MARKER = ".devopsmind_played"


def _has_active_workspace(lab_id: str):
    ws = WORKSPACE_DIR / lab_id
    return (
        ws.exists()
        and (ws / PLAY_MARKER).exists()
        and not (ws / ".devopsmind_success").exists()
    )


def _extract_basic_hint(hint):
    """
    Normalize hint formats:
    - str → return str
    - list → return first item
    - dict → return first list item, ignore 'detailed'
    """
    if isinstance(hint, str):
        return hint

    if isinstance(hint, list) and hint:
        return hint[0]

    if isinstance(hint, dict):
        for v in hint.values():
            if isinstance(v, list) and v:
                return v[0]

    return None


def load_hints_for_lab(lab_id: str):
    """
    INTERNAL helper for auto-hint system.
    """
    lab_dir = find_lab_by_id(lab_id)
    if not lab_dir:
        return []

    meta_file = lab_dir / "lab.yaml"
    if not meta_file.exists():
        return []

    meta = yaml.safe_load(meta_file.read_text()) or {}
    raw_hint = meta.get("hint")

    hints = []

    if isinstance(raw_hint, list):
        for h in raw_hint:
            basic = _extract_basic_hint(h)
            if basic:
                hints.append(basic)
    else:
        basic = _extract_basic_hint(raw_hint)
        if basic:
            hints.append(basic)

    return hints


def show_hint(lab_id: str):
    # -------------------------------------------------
    # 🔍 CHALLENGE EXISTENCE (AUTHORITATIVE)
    # -------------------------------------------------
    lab_dir = find_lab_by_id(lab_id)
    if not lab_dir:
        return Text(f"❌ Lab '{lab_id}' not found.", style="red")

    # -------------------------------------------------
    # 🔒 HARD REQUIRE: Safe Shell only
    # -------------------------------------------------
    if os.environ.get("DEVOPSMIND_SAFE") != "1":
        if _has_active_workspace(lab_id):
            return Text(
                "This lab is already in progress.\n"
                f"Run: `devopsmind resume {lab_id}` to resume the lab.",
                style="red",
            )

        return Text(
            "Lab is not active.\n"
            f"Run: `devopsmind start {lab_id}` to begin the lab.",
            style="red",
        )

    hints = load_hints_for_lab(lab_id)

    if hints:
        return Text(f"💡 Hint:\n\n{hints[0]}")

    return Text("❌ No hints available for this lab.", style="red")
