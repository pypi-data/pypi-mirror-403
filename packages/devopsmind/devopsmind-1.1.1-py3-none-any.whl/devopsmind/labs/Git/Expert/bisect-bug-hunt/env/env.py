#!/usr/bin/env python3
import os
import subprocess
import base64
from pathlib import Path

# -------------------------------------------------
# CONSTANTS (LOCKED)
# -------------------------------------------------
WORKSPACE_ROOT = Path("/workspace")
MARKER = WORKSPACE_ROOT / ".devopsmind_env_done"
GIT_DATE = "2020-01-01T00:00:00Z"


def run(cmd):
    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={
            **os.environ,
            "GIT_AUTHOR_DATE": GIT_DATE,
            "GIT_COMMITTER_DATE": GIT_DATE,
        },
    )


def seed():
    # -------------------------------------------------
    # Idempotency guard
    # -------------------------------------------------
    if MARKER.exists():
       # Repo already seeded, but secret must still be emitted
       os.chdir(WORKSPACE_ROOT)
       bug_commit = subprocess.check_output(
           ["git", "rev-parse", "HEAD~1"], text=True
       ).strip()
       print(f"DEVOPSMIND_SECRET_BISECT_COMMIT={bug_commit}")
       return

    # -------------------------------------------------
    # Initialize repo (ONLY ONCE)
    # -------------------------------------------------
    if (WORKSPACE_ROOT / ".git").exists():
        MARKER.write_text("done")
        return

    run(["git", "init"])
    run(["git", "branch", "-m", "main"])

    run(["git", "config", "--global", "user.name", "DevOpsMind"])
    run(["git", "config", "--global", "user.email", "devopsmind@local"])

    # Commit 1
    Path("app.py").write_text("def add(a, b): return a + b\n")
    run(["git", "add", "app.py"])
    run(["git", "commit", "-m", "Add add() function"])

    # Commit 2
    with open("app.py", "a") as f:
        f.write("def sub(a, b): return a - b\n")
    run(["git", "add", "app.py"])
    run(["git", "commit", "-m", "Add sub() function"])

    # Commit 3 — BUG INTRODUCED
    content = Path("app.py").read_text().replace("return a + b", "return a - b")
    Path("app.py").write_text(content)
    run(["git", "add", "app.py"])
    run(["git", "commit", "-m", "Refactor add logic"])

    bug_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()

    # -------------------------------------------------
    # 🔒 Emit ground truth for engine capture (stdout)
    # -------------------------------------------------
    print(f"DEVOPSMIND_SECRET_BISECT_COMMIT={bug_commit}")

    # Commit 4
    with open("app.py", "a") as f:
        f.write("print(add(2, 2))\n")
    run(["git", "add", "app.py"])
    run(["git", "commit", "-m", "Add debug print"])

    MARKER.write_text("done")


if __name__ == "__main__":
    seed()
