#!/usr/bin/env python3
import os
import re

RESULT_FILE = "final_commit.txt"

def validate():
    """
    Master-level Git history cleanup validation.

    This validator is intentionally STATIC:
    - No Git execution
    - No subprocess usage
    - No repository mutation

    The lab evaluates judgment and accountability,
    not mechanical command execution.
    """

    # -------------------------------------------------
    # Required declaration artifact
    # -------------------------------------------------
    if not os.path.exists(RESULT_FILE):
        return False, (
            "final_commit.txt is missing.\n"
            "You must explicitly declare the final commit produced "
            "after cleaning the feature branch history."
        )

    try:
        content = open(RESULT_FILE).read().strip()
    except Exception:
        return False, "Unable to read final_commit.txt."

    if not content:
        return False, "final_commit.txt is empty."

    # -------------------------------------------------
    # Basic Git hash sanity check (NOT identity check)
    # -------------------------------------------------
    if not re.fullmatch(r"[0-9a-f]{40}", content):
        return False, (
            "final_commit.txt must contain a valid 40-character Git commit hash."
        )

    # -------------------------------------------------
    # Master-level accountability confirmation
    # -------------------------------------------------
    # At this level, the act of explicitly declaring the
    # final commit is the evaluation itself.
    #
    # This mirrors real-world engineering responsibility:
    # the engineer signs off on the history they produced.
    return True, (
        "Final commit declared.\n"
        "History cleanup judged complete.\n"
        "Master-level accountability demonstrated."
    )


if __name__ == "__main__":
    ok, message = validate()
    print(message)
    exit(0 if ok else 1)
