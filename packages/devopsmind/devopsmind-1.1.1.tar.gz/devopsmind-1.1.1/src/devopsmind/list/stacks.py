from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.console import Group
from pathlib import Path
import yaml

from devopsmind.progress import load_state
from devopsmind.state import save_state
from devopsmind.constants import STACKS, STACK_COLORS, STACK_ICONS, BUNDLED_CHALLENGES
from devopsmind.tiers.tier_loader import load_visible_lab_ids
from devopsmind.handlers.progress_renderer import render_progress

# ✅ Backward-compatible ID normalization
from devopsmind.handlers.id_normalizer import canonical_id


TIERS_DIR = Path.home() / ".devopsmind" / "tiers"


def _load_tier_yaml(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception:
        return {}


def _load_foundation_only_ids() -> set[str]:
    """
    STRICT Foundation Core IDs only.
    Reads user-materialized foundation_core.yaml.
    """
    core = TIERS_DIR / "foundation_core.yaml"
    if not core.exists():
        return set()

    try:
        data = yaml.safe_load(core.read_text()) or {}
        return {canonical_id(cid) for cid in data.get("lab_ids", [])}
    except Exception:
        return set()


def _count_projects(tier: dict) -> int:
    """
    Projects are capstones.
    Count ONLY from tier YAML.
    """
    return len({
        canonical_id(pid)
        for pid in tier.get("project_ids", [])
    })


def _render_section(
    title: str,
    lab_ids: set[str],
    completed: set[str],
    state: dict,
    tier_key: str,
    project_count: int = 0,  # ✅ optional, backward-safe
) -> Panel:
    by_stack = {}

    normalized_completed = {canonical_id(c) for c in completed}
    normalized_lab_ids = {canonical_id(cid) for cid in lab_ids}

    for cid in normalized_lab_ids:
        for stack_dir in BUNDLED_CHALLENGES.iterdir():
            if not stack_dir.is_dir():
                continue

            for level_dir in stack_dir.iterdir():
                ch_dir = level_dir / cid
                if ch_dir.exists():
                    stack = stack_dir.name
                    by_stack.setdefault(stack, {"total": 0, "done": 0})
                    by_stack[stack]["total"] += 1

                    if cid in normalized_completed:
                        by_stack[stack]["done"] += 1

    # -------------------------------------------------
    # Title logic — ONLY change when projects exist
    # -------------------------------------------------
    if project_count:
        header = (
            f"{title}\n"
            f"[dim]Labs: {len(lab_ids)}  |  "
            f"Projects: {project_count}  |  "
            f"Total: {len(lab_ids) + project_count}[/dim]"
        )
    else:
        header = title

    table = Table(
        title=header,
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Stack / Area")
    table.add_column("Labs", justify="right")
    table.add_column("Progress")

    for stack, stats in sorted(by_stack.items()):
        progress = render_progress(
            stack=stack,
            done=stats["done"],
            total=stats["total"],
            state=state,
            tier_key=tier_key,
            mode="tier",
        )

        table.add_row(
            STACKS.get(stack, stack.replace("_", " ").title()),
            str(stats["total"]),
            progress,
        )

    return Panel(table, border_style="blue")


def show_my_stack_progress(section: str | None = None):
    """
    CLI View:
    - Foundation Core / Core Pro
    - Domain Pro sections
    - Domain Pro+ role sections
    """

    state = load_state() or {}

    completed = {
        canonical_id(c)
        for c in state.get("progress", {}).get("completed", [])
    }

    visible_ids = {
        canonical_id(cid)
        for cid in load_visible_lab_ids()
    }

    foundation_ids = _load_foundation_only_ids()

    sections = []

    # -------------------------------------------------
    # FOUNDATION / CORE PRO
    # -------------------------------------------------
    if section in (None, "foundation", "corepro"):
        available = {}

        for stack_dir in BUNDLED_CHALLENGES.iterdir():
            if not stack_dir.is_dir() or stack_dir.name.startswith("__"):
                continue

            total = 0
            done = 0

            for level_dir in stack_dir.iterdir():
                for ch_dir in level_dir.iterdir():
                    if not (ch_dir / "lab.yaml").exists():
                        continue

                    cid = canonical_id(ch_dir.name)

                    if cid not in foundation_ids:
                        continue

                    total += 1
                    if cid in completed:
                        done += 1

            if total:
                available[stack_dir.name] = (done, total)

        title = "📦 Foundation Core"
        if (TIERS_DIR / "core_pro.yaml").exists():
            title = "📦 Core Pro (including Foundation Core)"

        table = Table(
            title=title,
            show_header=True,
            header_style="bold cyan",
        )

        table.add_column("Stack")
        table.add_column("Labs", justify="right")
        table.add_column("Progress")

        for stack, (done, total) in sorted(available.items()):
            color = STACK_COLORS.get(stack, "white")
            icon = STACK_ICONS.get(stack, "📦")
            label = f"{icon} {STACKS.get(stack, stack.title())}"

            progress = render_progress(
                stack=stack,
                done=done,
                total=total,
                state=state,
                tier_key="foundation_core",
                stack_color=color,
                mode="foundation",
            )

            table.add_row(
                Text(label, style=color),
                str(total),
                progress,
            )

        sections.append(Panel(table, border_style="blue"))

    # -------------------------------------------------
    # DOMAIN PRO & DOMAIN PRO+
    # -------------------------------------------------
    tier_map = {
        "cloudops": ("domain_cloudops", "☁️ CloudOps"),
        "securityops": ("domain_security", "🔐 SecurityOps"),
        "observability": ("domain_observability", "📊 Observability"),
        "aiops": ("domain_aiops", "🤖 AI-Assisted Operations & Governance"),
        "scenarios": ("domain_scenarios", "🧩 Scenarios"),
        "story": ("domain_story", "📖 Story Mode"),
        "linux-admin": ("domain_plus_linux", "🎓 Role Track: Linux System Administrator"),
        "python-dev": ("domain_plus_python", "🎓 Role Track: Python Automation Engineer"),
    }

    for key, (prefix, title) in tier_map.items():
        if section not in (None, key):
            continue

        tier_file = next(TIERS_DIR.glob(f"{prefix}*.yaml"), None)
        if not tier_file:
            continue

        tier = _load_tier_yaml(tier_file)

        lab_ids = {
            canonical_id(cid)
            for cid in tier.get("lab_ids", [])
            if canonical_id(cid) in visible_ids
        }

        project_count = _count_projects(tier)

        if not lab_ids:
            continue

        sections.append(
            _render_section(
                title,
                lab_ids,
                completed,
                state,
                tier_key=prefix,
                project_count=project_count,
            )
        )

    # -------------------------------------------------
    # GLOBAL EXPLORE (ALWAYS LAST)
    # -------------------------------------------------
    sections.append(
        Panel(
            Group(
                Text("▶ Explore labs:", style="bold cyan"),
                Text("  devopsmind search <stack>", style="dim"),
                Text("  devopsmind search <stack> --level <level>", style="dim"),
                Text(""),
                Text("▶ Need guidance?", style="bold cyan"),
                Text("  devopsmind mentor", style="dim"),
            ),
            border_style="blue",
        )
    )

    save_state(state)
    return Group(*sections)


# -------------------------------------------------
# 🔎 Autocomplete helper
# -------------------------------------------------
from devopsmind.list.lab_resolver import list_all_labs, find_lab_by_id
from devopsmind.handlers.lab_utils import load_lab_metadata


def list_all_stacks():
    """
    Return a sorted list of all unique stack names.

    Used for:
    - autocomplete
    - search UX

    Must be fast and side-effect free.
    """
    stacks = set()

    for lab_id in list_all_labs():
        lab_dir = find_lab_by_id(lab_id)
        if not lab_dir:
            continue

        try:
            meta = load_lab_metadata(lab_dir)
        except Exception:
            continue

        stack = meta.get("stack")
        if stack:
            stacks.add(stack)

    return sorted(stacks)
