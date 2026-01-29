# src/devopsmind/handlers/validate_handler.py

from rich.text import Text
from rich.console import Group
import sys

from devopsmind.engine.engine import validate_only
from devopsmind.handlers.validate_ui import (
    show_validation_result,
    show_secret_reveal,
)
from devopsmind.achievements import list_badges

from devopsmind.handlers.id_normalizer import canonical_id
from devopsmind.handlers.ui_helpers import boxed

from devopsmind.list.lab_resolver import find_lab_by_id
import yaml


def handle_validate(args, console, boxed=boxed):
    console.clear()

    lab_id = canonical_id(args.id)

    # -------------------------------------------------
    # ❌ CHALLENGE NOT FOUND
    # -------------------------------------------------
    lab_dir = find_lab_by_id(lab_id)
    if not lab_dir:
        console.print(
            boxed(
                "❌ Validation Failed",
                Text(f"Lab '{lab_id}' not found.", style="red"),
            )
        )
        sys.exit(1)

    # -------------------------------------------------
    # 🔐 LOAD CHALLENGE XP
    # -------------------------------------------------
    xp = None
    meta_file = lab_dir / "lab.yaml"
    meta = {}

    if meta_file.exists():
        try:
            meta = yaml.safe_load(meta_file.read_text()) or {}
            xp = int(meta.get("xp", 0))
        except Exception:
            xp = 0

    # -------------------------------------------------
    # ▶ VALIDATE
    # -------------------------------------------------
    result = validate_only(lab_id, xp=xp)

    # -------------------------------------------------
    # ❌ FAILURE PATH  → EXIT CODE 1
    # -------------------------------------------------
    if isinstance(result, dict) and result.get("error"):
        body = [Text(result["error"], style="red")]

        auto_hint = result.get("auto_hint")
        if auto_hint:
            body += [Text(""), auto_hint]

        console.print(boxed("❌ Validation Failed", Group(*body)))
        sys.exit(1)

    # -------------------------------------------------
    # ✅ SUCCESS PATH → EXIT CODE 0
    # -------------------------------------------------
    ui_payload = {
        "lab_id": result.get("lab_id"),
        "stack": result.get("stack"),
        "difficulty": result.get("difficulty"),
        "skills": result.get("skills"),
        "earned_badges": result.get("earned_badges") or result.get("achievements"),
        "sync_status": result.get("sync_status"),
        "mentor_after": result.get("mentor_after"),
        "xp_message": result.get("xp_message"),
        "xp_awarded": result.get("xp_awarded"),
        "milestone_bonus": result.get("milestone_bonus"),
        "message": result.get("message"),
        "solution": meta.get("solution"),
    }

    console.print(
        boxed(
            f"🧪 Validate · {lab_id}",
            show_validation_result(**ui_payload),
        )
    )

    panel = show_secret_reveal(
        [
            a
            for a in list_badges(raw=True)
            if a["id"] in (result.get("earned_badges") or [])
            and a.get("category") == "secret"
        ]
    )
    if panel:
        console.print(panel)

    sys.exit(0)
