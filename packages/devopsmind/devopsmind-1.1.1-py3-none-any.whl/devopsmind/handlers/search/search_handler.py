# src/devopsmind/handlers/search/search_handler.py

from rich.table import Table
from rich.text import Text
from rich.console import Group
import yaml

from devopsmind.constants import BUNDLED_CHALLENGES, DIFFICULTY_ORDER
from devopsmind.handlers.search.difficulty import DIFFICULTY_XP, VALID_DIFFICULTIES
from devopsmind.progress import load_state
from devopsmind.tiers.tier_loader import load_visible_lab_ids


def normalize_level(level):
    if not level:
        return None
    return level.strip().capitalize()


def handle_search(args, console, boxed):
    term = args.term.lower()
    level_filter = normalize_level(args.level)

    # Validate level (case-insensitive support)
    if level_filter and level_filter not in VALID_DIFFICULTIES:
        console.print(
            boxed(
                "❌ Invalid Level",
                Text(
                    f"'{args.level}' is not a valid level.\n\n"
                    f"Valid levels:\n"
                    + ", ".join(sorted(VALID_DIFFICULTIES)),
                    style="red",
                ),
            )
        )
        return

    completed = set(load_state().get("progress", {}).get("completed", []))
    visible_ids = load_visible_lab_ids()

    table = Table(
        title=f"Search results for '{term}'",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Stack")
    table.add_column("Level")
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Effort", justify="right")
    table.add_column("Status")

    results = []

    for stack in BUNDLED_CHALLENGES.iterdir():
        if not stack.is_dir():
            continue

        for level in stack.iterdir():
            if not level.is_dir():
                continue

            # 🔹 LEVEL FILTER (HERE — CORRECT PLACE)
            if level_filter and level.name != level_filter:
                continue

            for ch in level.iterdir():
                meta_file = ch / "lab.yaml"
                if not meta_file.exists():
                    continue

                # Visibility filter
                if visible_ids and ch.name not in visible_ids:
                    continue

                meta = yaml.safe_load(meta_file.read_text()) or {}
                cid = meta.get("id", ch.name)
                title = meta.get("title", "")
                xp = str(DIFFICULTY_XP.get(level.name, meta.get("xp", 0)))
                status = "✅ Completed" if cid in completed else "❌ Pending"

                haystack = f"{stack.name} {level.name} {cid} {title}".lower()
                if term in haystack:
                    results.append(
                        (
                            stack.name,
                            level.name,
                            cid,
                            title,
                            xp,
                            status,
                        )
                    )

    if not results:
        console.print(
            boxed(
                "🔍 Search",
                Text("❌ No matching labs found.", style="yellow"),
            )
        )
        return

    # 🔑 Stable semantic ordering
    results.sort(
        key=lambda r: (
            r[0],
            DIFFICULTY_ORDER.get(r[1], 99),
            r[2],
        )
    )

    for row in results:
        table.add_row(*row)

    console.print(
        boxed(
            "🔍 Search",
            Group(
                table,
                Text(""),
                Text("▶ Start a lab:", style="bold cyan"),
                Text("  devopsmind start <ID>", style="dim"),
            ),
        )
    )
