from pathlib import Path

# Phrases that exist only in the template
# Presence of these means the user did not replace placeholders
PLACEHOLDER_PHRASES = [
    "Describe why",
    "What risks does it reduce",
    "What should happen",
    "How does automation",
    "Where should validation",
    "Capture any",
    "What benefits does it provide",
    "What is considered the source of truth",
    "How are changes applied",
    "How is rollback expected",
    "What responsibility does",
    "What should happen inside the container",
    "What assumptions",
]

def validate_design_file(path: Path):
    results = []
    design = path / "DESIGN.md"

    # ---------------- Missing file ----------------
    if not design.exists():
        results.append({
            "level": "improve",
            "symbol": "⚠️",
            "message": "DESIGN.md is missing",
            "why": "This file captures your design intent.",
            "suggestion": "Create DESIGN.md and replace the template placeholders.",
        })
        return results

    content = design.read_text(encoding="utf-8").strip()

    # ---------------- Empty file ----------------
    if not content:
        results.append({
            "level": "improve",
            "symbol": "⚠️",
            "message": "DESIGN.md is empty",
            "why": "Design intent must be written by you.",
            "suggestion": "Replace the template questions with your own explanations.",
        })
        return results

    # ---------------- Placeholder detection ----------------
    placeholder_hits = [
        phrase for phrase in PLACEHOLDER_PHRASES
        if phrase.lower() in content.lower()
    ]

    if placeholder_hits:
        results.append({
            "level": "improve",
            "symbol": "⚠️",
            "message": "DESIGN.md still contains template placeholders",
            "why": (
                "This file should reflect your own thinking, "
                "not the default template."
            ),
            "suggestion": (
                "Replace the template questions with your own explanations. "
                "You don’t need to write much — short answers are enough."
            ),
        })
    else:
        results.append({
            "level": "ok",
            "symbol": "✅",
            "message": "Design intent documented",
        })

    return results
