# src/devopsmind/handlers/progress_renderer.py

from rich.text import Text


def render_progress(
    *,
    stack: str,
    done: int,
    total: int,
    state: dict,
    tier_key: str,              # ✅ REQUIRED (foundation_core, domain_aiops, etc.)
    stack_color: str | None = None,
    mode: str = "foundation",   # foundation | tier
) -> Text:
    """
    STRICT progress semantics:

    FOUNDATION MODE:
    - Bar      → foundation labs completed ONLY
    - Coverage → foundation completion

    TIER MODE:
    - Bar      → tier labs completed
    - Coverage → tier completion

    NEW CONTENT:
    - Tracked ONCE per (tier + stack)
    """

    # -------------------------------------------------
    # 🔒 HARD ASSERTION (DO NOT REMOVE)
    # -------------------------------------------------
    assert isinstance(tier_key, str) and tier_key.strip(), (
        "render_progress() requires a non-empty 'tier_key'. "
        "This is mandatory to correctly scope progress tracking."
    )

    text = Text()

    # -------------------------------------------------
    # Progress bar (curriculum-based ONLY)
    # -------------------------------------------------
    segments = 5

    ratio = (done / total) if total > 0 else 0
    filled = round(ratio * segments)
    filled = max(0, min(segments, filled))

    bar = " ".join(
        ["●"] * filled + ["○"] * (segments - filled)
    )

    if stack_color:
        text.append(bar, style=stack_color)
    else:
        text.append(bar)

    text.append("  ")

    # -------------------------------------------------
    # Coverage percentage
    # -------------------------------------------------
    coverage = int(ratio * 100) if total > 0 else 0

    if done >= total and total > 0:
        text.append("✔", style="bold green")
    else:
        if coverage >= 60:
            style = "cyan"
        elif coverage >= 25:
            style = "yellow"
        else:
            style = "dim"

        text.append(f"Coverage {coverage}%", style=style)

    # -------------------------------------------------
    # New content detection (EDGE-triggered, TIER-SCOPED)
    # -------------------------------------------------
    seen_totals = state.setdefault("stack_seen_totals", {})
    key = f"{tier_key}:{stack}"

    last_seen = seen_totals.get(key)

    if last_seen is not None and last_seen > 0 and total > last_seen:
        text.append(f"  🕘(+{total - last_seen} new)", style="dim")

    seen_totals[key] = total

    return text
