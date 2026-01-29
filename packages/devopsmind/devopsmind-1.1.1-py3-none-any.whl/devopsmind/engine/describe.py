from pathlib import Path
from rich.markdown import Markdown
from rich.text import Text
from rich.align import Align
from rich.console import Group
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


def describe_lab(lab_id: str):
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

    desc = lab_dir / "description.md"
    if not desc.exists():
        return Text("❌ description.md missing.", style="red")

    lines = desc.read_text().splitlines()

    title_line = None
    body_lines = []

    # Extract first markdown heading as title
    for line in lines:
        if title_line is None and line.startswith("###"):
            title_line = line.replace("###", "").strip()
        else:
            body_lines.append(line)

    # Fallback: render normally if no title heading found
    if not title_line:
        return Markdown(desc.read_text(), justify="left")

    title = Align.center(Text(title_line, style="bold"))
    body = Markdown("\n".join(body_lines).strip(), justify="left")

    return Group(
        title,
        Text(""),
        body,
    )
