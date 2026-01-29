from pathlib import Path

PLACEHOLDER_PHRASES = [
    "Describe why",
    "What problems does it solve",
    "What responsibilities",
    "What is explicitly out of scope",
    "How do changes move",
    "What assumptions",
    "Capture any workflow",
]


def validate_git_design(path: Path):
    results = []
    design = path / "DESIGN.md"

    if not design.exists():
        results.append({
            "level": "improve",
            "symbol": "⚠️",
            "message": "Git DESIGN.md is missing",
            "why": "Version control decisions must be documented.",
            "suggestion": "Write a short explanation of how Git is used.",
        })
        return results

    content = design.read_text(encoding="utf-8").strip()

    if not content:
        results.append({
            "level": "improve",
            "symbol": "⚠️",
            "message": "Git DESIGN.md is empty",
            "why": "Design intent must be written by you.",
        })
        return results

    if any(p.lower() in content.lower() for p in PLACEHOLDER_PHRASES):
        results.append({
            "level": "improve",
            "symbol": "⚠️",
            "message": "Git DESIGN.md still contains template placeholders",
            "why": "This file should reflect your own Git workflow decisions.",
        })
        return results

    results.append({
        "level": "ok",
        "symbol": "✅",
        "message": "Git design intent documented",
    })

    return results
