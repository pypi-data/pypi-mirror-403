#!/usr/bin/env python3
import os
import sys

def validate():
    if not os.path.isdir("project"):
        return False, "Directory 'project' missing."

    notes = "project/notes.txt"
    if not os.path.exists(notes):
        return False, "notes.txt missing inside project."

    try:
        with open(notes) as f:
            content = f.read().strip()
    except Exception:
        return False, "Unable to read notes.txt."

    if content == "DevOpsMind":
        return True, "notes.txt contains the correct content."
    return False, "notes.txt content incorrect."

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)

