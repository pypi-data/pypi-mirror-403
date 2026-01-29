"""
Cloud restore decision logic

Rules:
- Restore is tied to USER ID, not installation
- Prompt only if:
  - cloud snapshot exists
  - user has not decided before
- Decision is stored locally
"""

from .snapshot import snapshot_exists, restore_snapshot
from devopsmind.state import (
    get_restore_decision,
    set_restore_decision,
    load_state,
    save_state,
)


def maybe_prompt_cloud_restore(user_public_id: str):
    """
    Ask user whether to restore cloud snapshot if:
    - snapshot exists
    - no prior decision stored
    """

    # No cloud data → nothing to do
    if not snapshot_exists(user_public_id):
        return

    # Decision already made → respect it
    decision = get_restore_decision(user_public_id)
    if decision is not None:
        return

    # Ask user
    choice = input(
        "☁️ Cloud progress found.\n"
        "Restore cloud progress now? [Y/n]: "
    ).strip().lower()

    decision = choice in ("", "y", "yes")
    set_restore_decision(user_public_id, decision)

    if not decision:
        return

    # -----------------------------
    # Perform restore
    # -----------------------------
    snapshot = restore_snapshot(user_public_id)

    # -----------------------------
    # ✅ XP RESTORE (SCHEMA-SAFE)
    # -----------------------------
    if isinstance(snapshot, dict):
        xp_block = snapshot.get("xp", {})

        # New snapshot schema (xp as dict)
        if isinstance(xp_block, dict):
            remote_labs = int(xp_block.get("labs", xp_block.get("total", 0)))
            remote_projects = int(xp_block.get("projects", 0))
        else:
            # Legacy snapshot (xp as int)
            remote_labs = int(xp_block or 0)
            remote_projects = 0

        state = load_state()

        state["xp"] = {
            "labs": remote_labs,
            "projects": remote_projects,
            "total": remote_labs + remote_projects,
        }

        save_state(state)
