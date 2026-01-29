import hashlib
import json
import requests
from datetime import datetime
from pathlib import Path

from devopsmind.progress import load_state, save_state
from devopsmind.constants import RELAY_URL


SNAPSHOT_PATH = Path.home() / ".devopsmind" / "snapshot.json"


# -------------------------------------------------
# 🏆 AUTHORITATIVE XP → RANK LADDER (LOCKED)
# -------------------------------------------------
XP_LEVELS = [
    (0, "Initiate"),
    (1000, "Operator"),
    (5000, "Executor"),
    (10000, "Controller"),
    (20000, "Automator"),
    (35000, "Coordinator"),
    (55000, "Orchestrator"),
    (80000, "Stabilizer"),
    (120000, "Observer"),
    (180000, "Scaler"),
    (260000, "Resilient"),
    (370000, "Fortified"),
    (520000, "Optimizer"),
    (750000, "Tuner"),
    (1_000_000, "Distributor"),
    (1_500_000, "Integrator"),
    (2_000_000, "Architected"),
    (3_000_000, "Autonomous"),
    (5_000_000, "Self-Healing"),
    (10_000_000, "Sovereign"),
]


def derive_rank_from_xp(labs_xp: int) -> str:
    current = XP_LEVELS[0][1]
    for threshold, rank in XP_LEVELS:
        if labs_xp >= threshold:
            current = rank
        else:
            break
    return current


# -------------------------------------------------
# Snapshot Builder (PURE DATA — NO UI)
# -------------------------------------------------
def build_snapshot(state=None):
    if state is None:
        state = load_state()

    profile = state.get("profile") or {}
    progress = state.get("progress") or {}

    # 🔧 CHANGE: preserve structured tier ownership
    tiers_owned = state.get("tiers", {}).get("owned", {})

    projects = state.get("projects", {})

    xp = state.get("xp", {})
    labs_xp = int(xp.get("labs", 0))
    rank = derive_rank_from_xp(labs_xp)

    return {
        "schema": "v3.4",

        # 🔐 Identity
        "email_hash": profile.get("email_hash"),
        "user_public_id": profile.get("user_public_id"),
        "username": profile.get("username"),
        "handle": profile.get("gamer"),

        # 🔢 XP (STRUCTURED — SAME AS state.json)
        "xp": {
            "labs": int(xp.get("labs", 0)),
            "projects": int(xp.get("projects", 0)),
            "total": int(xp.get("total", 0)),
        },

        "rank": rank,

        # 🔢 Progress
        "completed_labs": progress.get("completed", []),
        "badges": state.get("badges", []),
        "by_stack": progress.get("by_stack", {}),
        "by_difficulty": progress.get("by_difficulty", {}),
        "by_stack_difficulty": progress.get("by_stack_difficulty", {}),

        # 📦 Projects
        "projects": projects,

        # 🎟️ Tier ownership (AUTHORITATIVE, STRUCTURED)
        "tiers_owned": tiers_owned,

        "updated_at": datetime.utcnow().isoformat() + "Z",
    }


# -------------------------------------------------
# Snapshot Signing (INTEGRITY ONLY)
# -------------------------------------------------
def sign_snapshot(snapshot, email_hash):
    signing_view = {
        "schema": snapshot.get("schema"),
        "email_hash": snapshot.get("email_hash"),
        "rank": snapshot.get("rank"),
        "xp": snapshot.get("xp"),
        "completed_labs": snapshot.get("completed_labs", []),
        "badges": snapshot.get("badges", []),
        "by_stack": snapshot.get("by_stack", {}),
        "by_difficulty": snapshot.get("by_difficulty", {}),
        "by_stack_difficulty": snapshot.get("by_stack_difficulty", {}),
        "tiers_owned": snapshot.get("tiers_owned", {}),
        "projects": snapshot.get("projects", {}),
    }

    canonical = json.dumps(signing_view, sort_keys=True)
    digest = hashlib.sha256((canonical + email_hash).encode()).hexdigest()

    signed = dict(snapshot)
    signed["signature"] = digest

    publish_to_leaderboard(signed)
    return signed


# -------------------------------------------------
# 🔐 Snapshot Verification
# -------------------------------------------------
def verify_snapshot(snapshot: dict, email_hash: str) -> bool:
    try:
        signing_view = {
            "schema": snapshot.get("schema"),
            "email_hash": snapshot.get("email_hash"),
            "rank": snapshot.get("rank"),
            "xp": snapshot.get("xp"),
            "completed_labs": snapshot.get("completed_labs", []),
            "badges": snapshot.get("badges", []),
            "by_stack": snapshot.get("by_stack", {}),
            "by_difficulty": snapshot.get("by_difficulty", {}),
            "by_stack_difficulty": snapshot.get("by_stack_difficulty", {}),
            "tiers_owned": snapshot.get("tiers_owned", {}),
            "projects": snapshot.get("projects", {}),
        }

        canonical = json.dumps(signing_view, sort_keys=True)
        expected = hashlib.sha256((canonical + email_hash).encode()).hexdigest()

        return snapshot.get("signature") == expected
    except Exception:
        return False


# -------------------------------------------------
# 📤 Leaderboard Publisher
# -------------------------------------------------
def publish_to_leaderboard(snapshot):
    try:
        payload = {
            "user_public_id": snapshot.get("user_public_id"),
            "handle": snapshot.get("handle"),
            "username": snapshot.get("username"),
            "xp": snapshot.get("xp", {}).get("total", 0),
            "rank": snapshot.get("rank"),
        }

        requests.post(
            f"{RELAY_URL}/leaderboard/write",
            json=payload,
            timeout=5,
        )
    except Exception:
        pass


# -------------------------------------------------
# 🔍 Snapshot existence probe
# -------------------------------------------------
def snapshot_exists(user_public_id: str, email_hash: str = None) -> bool:
    try:
        if email_hash is None:
            state = load_state()
            email_hash = state.get("profile", {}).get("email_hash")

        payload = {"user_public_id": user_public_id}
        if email_hash:
            payload["email_hash"] = email_hash

        res = requests.post(
            f"{RELAY_URL}/snapshot/exists",
            json=payload,
            timeout=5,
        )
        if res.status_code != 200:
            return False

        return res.json().get("exists") is True
    except Exception:
        return False


# -------------------------------------------------
# 🔓 Materialize owned tiers (NO LICENSE, VERSION-AWARE)
# -------------------------------------------------
def _materialize_owned_tier(tier_name: str, meta: dict):
    """
    Snapshot is authoritative.
    Materialize the exact tier version owned.
    No license checks.
    Never upgrades.
    Never downgrades.
    Offline-safe.
    """
    if tier_name == "foundation_core":
        return

    version = meta.get("version")
    if not isinstance(version, int):
        return

    base_dir = Path(__file__).parent.parent / "tiers"

    if tier_name == "core_pro":
        tier_dir = base_dir / "core_pro"

    elif tier_name.startswith("domain_plus_"):
        role = tier_name.removeprefix("domain_plus_")
        tier_dir = base_dir / role

    elif tier_name.startswith("domain_"):
        domain = tier_name.removeprefix("domain_")
        tier_dir = base_dir / domain

    else:
        return

    if not tier_dir.exists():
        return

    for f in tier_dir.glob(f"*_v{version}.yaml"):
        user_tiers = Path.home() / ".devopsmind" / "tiers"
        user_tiers.mkdir(parents=True, exist_ok=True)

        target = user_tiers / f.name
        if target.exists():
            return

        try:
            tmp = target.with_suffix(".tmp")
            tmp.write_text(f.read_text())
            tmp.replace(target)
        except Exception:
            pass
        return


# -------------------------------------------------
# 🔄 Snapshot restore (STRUCTURE-SAFE)
# -------------------------------------------------
def restore_snapshot(user_public_id: str, email_hash: str = None):
    state = load_state()
    preserved_auth = state.get("auth")

    email_hash = email_hash or state.get("profile", {}).get("email_hash")
    if not email_hash:
        raise RuntimeError("email_hash required for snapshot restore")

    res = requests.post(
        f"{RELAY_URL}/snapshot/get",
        json={"user_public_id": user_public_id, "email_hash": email_hash},
        timeout=10,
    )

    if res.status_code != 200:
        raise RuntimeError("Failed to restore snapshot")

    snapshot = res.json()
    verify_snapshot(snapshot, email_hash)

    state["profile"] = {
        "username": snapshot.get("username"),
        "gamer": snapshot.get("handle"),
        "user_public_id": user_public_id,
        "email_hash": email_hash,
    }

    state["progress"] = {
        "completed": snapshot.get("completed_labs", []),
        "by_stack": snapshot.get("by_stack", {}),
        "by_difficulty": snapshot.get("by_difficulty", {}),
        "by_stack_difficulty": snapshot.get("by_stack_difficulty", {}),
    }

    state["badges"] = snapshot.get("badges", [])
    state["xp"] = snapshot.get("xp", {})
    state["projects"] = snapshot.get("projects", {})

    # 🔧 CHANGE: merge structured tier ownership safely
    snapshot_tiers = snapshot.get("tiers_owned", {})

    tiers = state.setdefault("tiers", {})
    owned = tiers.get("owned", {})

    # 🔧 NORMALIZE: upgrade old list-based tiers to dict
    if isinstance(owned, list):
        owned = {tier: {} for tier in owned}
        tiers["owned"] = owned

    # Backward compatibility: old snapshots (list)
    if isinstance(snapshot_tiers, list):
        for tier in snapshot_tiers:
            owned.setdefault(tier, {})
            _materialize_owned_tier(tier, owned[tier])

    # New structured snapshots (dict)
    elif isinstance(snapshot_tiers, dict):
        for tier, meta in snapshot_tiers.items():
            owned[tier] = meta
            _materialize_owned_tier(tier, meta)

    if preserved_auth:
        state["auth"] = preserved_auth

    save_state(state)
    return snapshot
