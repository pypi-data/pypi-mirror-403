#!/usr/bin/env python3
from pathlib import Path
import sys

def validate():
    analysis_path = Path("impact-analysis.md")
    manifests_dir = Path("manifests")

    if not analysis_path.exists():
        return False, "impact-analysis.md not found."

    required_files = [
        "application-a.yaml",
        "application-b.yaml",
        "shared-manifest.yaml",
        "dependency-map.md",
    ]

    for f in required_files:
        if not (manifests_dir / f).exists():
            return False, f"Required manifest missing: manifests/{f}"

    try:
        analysis = analysis_path.read_text(encoding="utf-8")
    except Exception:
        return False, "Unable to read impact-analysis.md."

    required_sections = [
        "Shared Configuration",
        "Affected Applications",
        "Failure Propagation",
        "Blast Radius Reduction"
    ]

    for section in required_sections:
        if section not in analysis:
            return False, f"Missing required section: {section}"

    text = analysis.lower()

    # Evidence awareness
    if "application-a" not in text:
        return False, "Analysis must reference application-a."

    if "application-b" not in text:
        return False, "Analysis must reference application-b."

    if "shared" not in text or "configmap" not in text:
        return False, "Analysis must clearly identify shared configuration."

    # Reject untouched template text
    template_markers = [
        "identify the shared",
        "list all",
        "explain how",
        "propose one"
    ]

    for marker in template_markers:
        if marker in text:
            return False, (
                "Template text detected. "
                "Expert-level analysis must replace all instructional language."
            )

    # Depth requirement (Expert)
    if len(analysis.split()) < 300:
        return False, (
            "Analysis is too shallow for Expert level. "
            "Provide deeper system-level reasoning."
        )

    return True, "GitOps blast radius analysis is thorough and architecture-focused."

if __name__ == "__main__":
    ok, message = validate()
    print(message)
    sys.exit(0 if ok else 1)
