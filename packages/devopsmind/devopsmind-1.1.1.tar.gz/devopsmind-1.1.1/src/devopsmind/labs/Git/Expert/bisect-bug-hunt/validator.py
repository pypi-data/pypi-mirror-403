#!/usr/bin/env python3
import os
import sys
import re

from devopsmind.progress import load_state

USER_RESULT_FILE = "bug_commit.txt"
CHALLENGE_ID = "bisect-bug-hunt"


def _read_expected_commit():
    """
    Reads the expected commit hash from DevOpsMind persistent state.
    """
    state = load_state()
    secret = (
        state
        .get("lab_secrets", {})
        .get(CHALLENGE_ID)
    )

    if not isinstance(secret, dict):
        return None, "Internal validation error: missing ground truth."

    commit = secret.get("DEVOPSMIND_SECRET_BISECT_COMMIT")
    if not commit:
        return None, "Internal validation error: missing ground truth."

    return commit.strip(), None


def _read_user_commit():
    """
    Reads the learner-submitted commit hash.
    """
    if not os.path.exists(USER_RESULT_FILE):
        return None, "bug_commit.txt is missing."

    try:
        content = open(USER_RESULT_FILE).read().strip()
    except Exception:
        return None, "Unable to read bug_commit.txt."

    if not content:
        return None, "bug_commit.txt is empty."

    return content, None


def _is_valid_commit_hash(value):
    """
    Basic sanity check for a Git commit hash.
    """
    return bool(re.fullmatch(r"[0-9a-f]{40}", value))


def validate():
    expected_commit, err = _read_expected_commit()
    if err:
        return False, err

    user_commit, err = _read_user_commit()
    if err:
        return False, err

    if not _is_valid_commit_hash(user_commit):
        return False, (
            "bug_commit.txt must contain a full 40-character Git commit hash."
        )

    if user_commit != expected_commit:
        return False, (
            "Incorrect commit identified. "
            "The selected commit does not match the commit where the regression was introduced."
        )

    return True, (
        "Regression introduction commit correctly identified through Git history analysis."
    )


if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
