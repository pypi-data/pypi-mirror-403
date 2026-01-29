# src/devopsmind/programs/cli/submit.py

"""
devopsmind program submit <program>

Rules (LOCKED):
- submit MUST be invoked from inside the safe program shell
- actual submission & certificate generation happens on the host
- user stays inside the shell
"""

import json
import subprocess
import os
from pathlib import Path
from datetime import datetime, timezone

from rich.console import Group, Console
from rich.text import Text

from devopsmind.programs.ui import boxed_program
from devopsmind.programs.loader import load_program
from devopsmind.programs.policy_loader import load_policy, get_program_status
from devopsmind.programs.state import load_program_state

# 🔹 OUTBOX TRIGGER
from devopsmind.programs.outbox.trigger import trigger_outbox_processor


console = Console()

# --------------------------------------------------
# Paths
# --------------------------------------------------

DEVOPSMIND_HOME = Path.home() / ".devopsmind"
PROGRAMS_DIR = DEVOPSMIND_HOME / "programs"
PROGRAM_SRC_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------
# Utilities
# --------------------------------------------------

def _program_root(program: str) -> Path:
    return PROGRAMS_DIR / program


def _ensure_certificate_identity_from_state(program_dir: Path):
    state_file = Path.home() / ".devopsmind" / "state.json"

    if not state_file.exists():
        raise RuntimeError("User state not found.")

    state = json.loads(state_file.read_text())
    full_name = state.get("profile", {}).get("username")

    if not full_name or not full_name.strip():
        raise RuntimeError("Certificate name missing.")

    identity_file = program_dir / "certificate_identity.json"
    identity_file.parent.mkdir(parents=True, exist_ok=True)

    identity_file.write_text(
        json.dumps(
            {
                "full_name": full_name.strip(),
                "confirmed_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
    )


# --------------------------------------------------
# Completion checks
# --------------------------------------------------

def _load_manifest(program: str) -> dict | None:
    manifest = (
        PROGRAM_SRC_ROOT
        / "programs"
        / program
        / "checks"
        / "manifest.json"
    )
    if not manifest.exists():
        return None
    return json.loads(manifest.read_text())


def _run_completion_checks(program: str, workspace: Path) -> list[str]:
    manifest = _load_manifest(program)
    if not manifest:
        return ["No completion manifest found"]

    checks_dir = (
        PROGRAM_SRC_ROOT
        / "programs"
        / program
        / "checks"
    )

    failures: list[str] = []

    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROGRAM_SRC_ROOT.parent)

    for check in manifest.get("required", []):
        label = check.get("label", check.get("id", "Unnamed Check"))
        script = checks_dir / check.get("script", "")

        if not script.exists():
            failures.append(f"{label}: missing check script")
            continue

        result = subprocess.run(
            ["python3", str(script)],
            capture_output=True,
            text=True,
            env=env,
            cwd=workspace,
        )

        if result.returncode != 0:
            reason = (
                result.stdout.strip()
                or result.stderr.strip()
                or "check failed"
            )
            failures.append(f"{label}: {reason}")

    return failures


# --------------------------------------------------
# Outbox
# --------------------------------------------------

def _create_outbox_entry(program: str, program_dir: Path):
    outbox = program_dir / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)

    entry = {
        "type": "certificate_email",
        "program": program,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
    }

    filename = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        + f"-{program}.json"
    )

    (outbox / filename).write_text(json.dumps(entry, indent=2))


# --------------------------------------------------
# Main handler
# --------------------------------------------------

def handle_program_submit(args):
    """
    submit:
    - allowed ONLY inside safe shell
    - forwarded ONCE to host for execution
    """

    program = os.environ.get("DEVOPSMIND_PROGRAM")
    bridged = os.environ.get("DEVOPSMIND_SUBMIT_BRIDGE")

    # ==================================================
    # 🚫 BLOCK direct host execution
    # ==================================================
    if not program and not bridged:
        return boxed_program(
            "🧠 Program Submission",
            Text(
                "❌ Program submission must be run from inside the program shell.\n\n"
                "To enter the program:\n\n"
                "  devopsmind program <program>\n\n"
                "Then inside the shell:\n\n"
                "  devopsmind program submit",
                style="red",
            ),
        )

    # ==================================================
    # 🔁 SAFE SHELL → HOST FORWARD
    # ==================================================
    if program and not bridged:
        console.print(
            "\n⏳ Generating certificate on host environment...\n"
            "This may take a few seconds.\n",
            style="yellow",
        )

        host_env = os.environ.copy()
        host_env.pop("DEVOPSMIND_PROGRAM", None)
        host_env["DEVOPSMIND_SUBMIT_BRIDGE"] = "1"

        subprocess.run(
            ["devopsmind", "program", "submit", program],
            env=host_env,
            check=False,
        )

        # stay inside shell
        return None

    # ==================================================
    # 🏁 HOST EXECUTION (REAL SUBMIT)
    # ==================================================
    program = args[0] if args else None
    if not program:
        return boxed_program(
            "🧠 Program Submission",
            Text("Internal submit error: program not resolved.", style="red"),
        )

    program_dir = _program_root(program)

    data = load_program(program)
    if not data:
        return boxed_program(
            "🧠 Program Submission",
            Text(f"Program '{program}' not found.", style="red"),
        )

    policy = load_policy(program)
    status = get_program_status(policy) if policy else "UNKNOWN"
    if status != "ACTIVE":
        return boxed_program(
            "🧠 Program Submission",
            Text(f"Program is not active ({status}).", style="red"),
        )

    completed_file = program_dir / ".completed"
    if completed_file.exists():
        return boxed_program(
            "🧠 Program Submission",
            Text(
                "Program already completed and certified.",
                style="yellow",
            ),
        )

    workspace = data["workspace"]
    failures = _run_completion_checks(program, workspace)
    if failures:
        return boxed_program(
            "🧠 Program Submission",
            Text(
                "Submission blocked. Incomplete requirements:\n\n"
                + "\n".join(f"• {f}" for f in failures),
                style="red",
            ),
        )

    try:
        _ensure_certificate_identity_from_state(program_dir)
    except Exception as e:
        return boxed_program(
            "🧠 Program Submission",
            Text(str(e), style="red"),
        )

    from devopsmind.programs.buildtrack.cert.generator import generate_certificate

    # ==================================================
    # 🎓 CERT GENERATION + OUTBOX
    # ==================================================

    generate_certificate(program, program_dir)
    _create_outbox_entry(program, program_dir)

    # 🔹 AUTO-TRIGGER OUTBOX PROCESSOR (HOST ONLY)
    trigger_outbox_processor(program_dir)

    completed_file.write_text(
        json.dumps(
            {
                "status": "completed",
                "certified": True,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
    )

    return Group(
        boxed_program(
            "🎓 Program Certified",
            Text(
                "Program completed successfully.\n\n"
                "Certificate generated locally.\n"
                "Email delivery will occur when possible.",
                style="green",
            ),
        )
    )
