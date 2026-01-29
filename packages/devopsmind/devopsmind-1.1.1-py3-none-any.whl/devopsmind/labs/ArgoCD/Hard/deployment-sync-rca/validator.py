#!/usr/bin/env python3
from pathlib import Path
import sys

def validate():
    rca_path = Path("rca.md")
    manifests_dir = Path("manifests")

    required_files = [
        "application.yaml",
        "sync-events.log",
        "failure-timeline.md",
    ]

    if not rca_path.exists():
        return False, "rca.md not found."

    if not manifests_dir.exists():
        return False, "manifests directory missing."

    for f in required_files:
        if not (manifests_dir / f).exists():
            return False, f"Required evidence missing: manifests/{f}"

    try:
        rca = rca_path.read_text(encoding="utf-8")
    except Exception:
        return False, "Unable to read rca.md."

    required_sections = [
        "Observed Failure",
        "Root Cause",
        "Contributing Factors",
        "Corrective Action"
    ]

    for section in required_sections:
        if section not in rca:
            return False, f"Missing required section: {section}"

    lowered = rca.lower()

    # Evidence awareness (Hard tier)
    if "configmap" not in lowered:
        return False, "RCA must reference the missing ConfigMap identified in sync events."

    if "sync" not in lowered:
        return False, "RCA must explicitly reference the sync failure."

    # Reject untouched template language
    template_markers = [
        "describe what failed",
        "identify the primary reason",
        "list any additional factors",
        "describe one action"
    ]

    for marker in template_markers:
        if marker in lowered:
            return False, (
                "Template text detected. "
                "Hard-level RCA must replace all instructional language."
            )

    # Depth check
    if len(rca.split()) < 200:
        return False, (
            "RCA is too shallow for Hard level. "
            "Provide a detailed, evidence-backed analysis."
        )

    return True, "Root Cause Analysis is complete, evidence-based, and review-ready."

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
