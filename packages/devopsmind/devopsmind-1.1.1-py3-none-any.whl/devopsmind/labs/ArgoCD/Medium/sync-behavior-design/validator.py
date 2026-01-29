#!/usr/bin/env python3
from pathlib import Path
import sys

def validate():
    """
    Medium-level Argo CD sync behavior validation.

    - Offline-safe
    - Deterministic
    - Requires explicit configuration and explanation
    """

    app_path = Path("application.yaml")
    notes_path = Path("sync-notes.md")

    if not app_path.exists():
        return False, (
            "Application definition not found.\n"
            "The file `application.yaml` must exist."
        )

    if not notes_path.exists():
        return False, (
            "Sync behavior notes not found.\n"
            "The file `sync-notes.md` must exist."
        )

    try:
        app = app_path.read_text(encoding="utf-8")
    except Exception:
        return False, "Unable to read application.yaml."

    try:
        notes = notes_path.read_text(encoding="utf-8")
    except Exception:
        return False, "Unable to read sync-notes.md."

    required_fields = [
        "syncPolicy:",
        "automated:",
        "prune:",
        "selfHeal:"
    ]

    for field in required_fields:
        if field not in app:
            return False, (
                f"Missing required sync configuration: {field}\n"
                "Automated sync behavior must be fully defined."
            )

    for line in app.splitlines():
        if line.strip().startswith("prune:") and not line.split("prune:", 1)[1].strip():
            return False, "Prune behavior is declared but not configured."

        if line.strip().startswith("selfHeal:") and not line.split("selfHeal:", 1)[1].strip():
            return False, "Self-heal behavior is declared but not configured."

    notes_lower = notes.lower()

    if "drift" not in notes_lower:
        return False, (
            "Sync behavior notes do not explain drift handling.\n"
            "Medium-level labs require explicit design reasoning."
        )

    if "fail" not in notes_lower:
        return False, (
            "Sync behavior notes do not explain sync failure handling."
        )

    placeholders = [
        "describe how argo cd reacts",
        "describe what happens",
    ]

    for placeholder in placeholders:
        if placeholder in notes_lower:
            return False, (
                "Sync behavior notes still contain template text.\n"
                "Replace placeholders with explicit design decisions."
            )

    return True, (
        "Argo CD sync behavior is clearly defined and documented.\n"
        "Automated sync, drift handling, and failure visibility are review-ready."
    )

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
