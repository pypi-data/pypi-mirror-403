from pathlib import Path
import yaml
from rich.table import Table
from rich.text import Text
from rich.console import Group

from devopsmind.constants import BUNDLED_CHALLENGES, DIFFICULTY_ORDER
from devopsmind.progress import load_state
from devopsmind.tiers.tier_loader import load_visible_lab_ids


def _load_completed():
    state = load_state()
    return set(state.get("progress", {}).get("completed", []))


def list_labs(stack: str | None = None):
    completed = _load_completed()

    # ---------------------------------------
    # Load visible lab IDs (FOUNDATION + OWNED TIERS)
    # ---------------------------------------
    visible_ids = load_visible_lab_ids()

    # -------------------------
    # STACK FILTER MODE
    # -------------------------
    if stack:
        stack_dir = None
        for s in BUNDLED_CHALLENGES.iterdir():
            if s.is_dir() and s.name.lower() == stack.lower():
                stack_dir = s
                break

        if not stack_dir:
            return Text(f"❌ Stack '{stack}' not found.", style="red")

        table = Table(
            title=f"{stack_dir.name} Labs",
            show_header=True,
            header_style="bold",
        )
        table.add_column("Level")
        table.add_column("ID")
        table.add_column("Title")
        table.add_column("XP", justify="right")
        table.add_column("Status")

        # 🔑 Semantic difficulty ordering (NOT alphabetical)
        levels = sorted(
            [d for d in stack_dir.iterdir() if d.is_dir()],
            key=lambda d: DIFFICULTY_ORDER.get(d.name, 99),
        )

        for level in levels:
            for ch in sorted(level.iterdir()):
                meta_file = ch / "lab.yaml"
                if not meta_file.exists():
                    continue

                # ---------------------------------------
                # Visibility filter
                # Only labs owned by the user
                # ---------------------------------------
                if visible_ids and ch.name not in visible_ids:
                    continue

                meta = yaml.safe_load(meta_file.read_text()) or {}
                cid = meta.get("id", ch.name)
                title = meta.get("title", "-")
                xp = str(meta.get("xp", 0))
                status = "✅ Completed" if cid in completed else "❌ Pending"

                table.add_row(
                    level.name,
                    cid,
                    title,
                    xp,
                    status,
                )

        return Group(
            table,
            Text(""),
            Text("▶ Start a lab:", style="bold cyan"),
            Text("  devopsmind start <ID>", style="dim"),
        )

    # -------------------------
    # STACK OVERVIEW MODE
    # -------------------------
    table = Table(
        title="Available Stacks",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Stack")
    table.add_column("Labs", justify="right")

    for stack_dir in sorted(BUNDLED_CHALLENGES.iterdir()):
        if not stack_dir.is_dir():
            continue

        # 🚫 Skip internal/system directories
        if stack_dir.name.startswith("__"):
            continue

        count = 0
        for level in stack_dir.iterdir():
            if not level.is_dir():
                continue

            for ch in level.iterdir():
                if not (ch / "lab.yaml").exists():
                    continue

                # ---------------------------------------
                # Visibility filter
                # ---------------------------------------
                if visible_ids and ch.name not in visible_ids:
                    continue

                count += 1

        # 🚫 Skip empty / invalid stacks
        if count == 0:
            continue

        table.add_row(stack_dir.name, str(count))

    return table


def search_labs(term: str):
    term = term.lower()
    completed = _load_completed()

    # ---------------------------------------
    # Load visible lab IDs
    # ---------------------------------------
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
    table.add_column("XP", justify="right")
    table.add_column("Status")

    results = []

    for stack in BUNDLED_CHALLENGES.iterdir():
        if not stack.is_dir():
            continue

        for level in stack.iterdir():
            if not level.is_dir():
                continue

            for ch in level.iterdir():
                meta_file = ch / "lab.yaml"
                if not meta_file.exists():
                    continue

                # ---------------------------------------
                # Visibility filter
                # ---------------------------------------
                if visible_ids and ch.name not in visible_ids:
                    continue

                meta = yaml.safe_load(meta_file.read_text()) or {}
                cid = meta.get("id", ch.name)
                title = meta.get("title", "")
                xp = str(meta.get("xp", 0))
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
        return Text("❌ No matching labs found.", style="yellow")

    # 🔑 Stable semantic ordering for search results
    results.sort(
        key=lambda r: (
            r[0],  # Stack
            DIFFICULTY_ORDER.get(r[1], 99),  # Difficulty
            r[2],  # ID
        )
    )

    for row in results:
        table.add_row(*row)

    return Group(
        table,
        Text(""),
        Text("▶ Start a lab:", style="bold cyan"),
        Text("  devopsmind start <ID>", style="dim"),
    )
