# src/devopsmind/handlers/xp_bar.py

from devopsmind.constants import XP_LEVELS


# -------------------------------------------------
# 🔢 XP formatter (DISPLAY ONLY)
# -------------------------------------------------
def _format_xp(value: int) -> str:
    try:
        value = int(value)
    except Exception:
        return "0"

    if value < 1_000:
        return str(value)

    if value < 1_000_000:
        v = value / 1_000
        return f"{v:.1f}k".rstrip("0").rstrip(".")

    if value < 1_000_000_000:
        v = value / 1_000_000
        return f"{v:.1f}M".rstrip("0").rstrip(".")

    v = value / 1_000_000_000
    return f"{v:.1f}B".rstrip("0").rstrip(".")


# -------------------------------------------------
# 🔧 XP normalization
# -------------------------------------------------
def _extract_xp(xp):
    """
    Returns:
    - rank_xp  → LAB XP only
    - total_xp → LAB + PROJECT XP (effort)
    """
    if isinstance(xp, int):
        return xp, xp

    if isinstance(xp, dict):
        labs = int(xp.get("labs", 0))
        projects = int(xp.get("projects", 0))
        return labs, labs + projects

    return 0, 0


def compute_rank_progress(xp, bar_width: int = 10):
    """
    Rank:
    - LAB XP only

    Display:
    - progress / total → rank window
    - effort_fmt → total XP earned
    """

    rank_xp, total_xp = _extract_xp(xp)

    current_rank = XP_LEVELS[0][1]
    next_rank = None
    prev_threshold = 0
    next_threshold = None

    for threshold, name in XP_LEVELS:
        if rank_xp >= threshold:
            current_rank = name
            prev_threshold = threshold
        else:
            next_threshold = threshold
            next_rank = name
            break

    # ---------------- MAX RANK ----------------
    if next_threshold is None:
        return {
            "current_rank": current_rank,
            "next_rank": None,
            "progress": total_xp,
            "total": total_xp,
            "progress_fmt": _format_xp(total_xp),
            "total_fmt": _format_xp(total_xp),
            "effort_fmt": _format_xp(total_xp),  # ✅ ADD
            "percent": 100,
            "filled": bar_width,
            "empty": 0,
        }

    # ------------- PROGRESS WINDOW -------------
    progress = max(0, total_xp - prev_threshold)
    total = max(1, next_threshold - prev_threshold)

    ratio = min(progress / total, 1.0)
    percent = int(ratio * 100)

    if progress == 0:
        filled = 1
    elif progress > 0:
        filled = max(1, int(ratio * bar_width))
    else:
        filled = 0

    empty = max(0, bar_width - filled)

    return {
        "current_rank": current_rank,
        "next_rank": next_rank,
        "progress": progress,
        "total": total,
        "progress_fmt": _format_xp(progress),
        "total_fmt": _format_xp(total),
        "effort_fmt": _format_xp(total_xp),  # ✅ ADD
        "percent": percent,
        "filled": filled,
        "empty": empty,
    }
