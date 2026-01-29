from pathlib import Path

def validate_shell_scripts(path: Path):
    results = []
    scripts = list(path.glob("*.sh"))

    if not scripts:
        results.append({
            "level": "improve",
            "symbol": "⚠️",
            "message": "No shell scripts found",
            "why": "Shell scripts represent OS-level responsibilities.",
            "suggestion": "Add at least one .sh file.",
        })
        return results

    for script in scripts:
        first_line = script.read_text().splitlines()[0] if script.read_text() else ""
        if not first_line.startswith("#!"):
            results.append({
                "level": "info",
                "symbol": "ℹ️",
                "message": f"{script.name} has no shebang",
                "why": "Shebangs clarify script intent.",
                "suggestion": "Consider adding a shebang line.",
            })

    results.append({
        "level": "ok",
        "symbol": "✅",
        "message": "Shell scripts present",
    })

    return results
