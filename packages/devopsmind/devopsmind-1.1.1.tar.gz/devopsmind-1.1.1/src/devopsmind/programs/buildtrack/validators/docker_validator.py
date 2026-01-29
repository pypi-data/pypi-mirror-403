from pathlib import Path

VALID_INSTRUCTIONS = {
    "FROM", "RUN", "CMD", "ENTRYPOINT", "COPY", "ADD",
    "WORKDIR", "ENV", "EXPOSE", "ARG", "LABEL"
}

def validate_dockerfile(path: Path):
    results = []
    dockerfile = path / "Dockerfile"

    if not dockerfile.exists():
        results.append({
            "level": "improve",
            "symbol": "⚠️",
            "message": "Dockerfile is missing",
            "why": "Dockerfile represents how execution is packaged.",
            "suggestion": "Create a Dockerfile that reflects your design.",
        })
        return results

    lines = dockerfile.read_text().splitlines()

    if not any(l.strip().startswith("FROM") for l in lines):
        results.append({
            "level": "improve",
            "symbol": "⚠️",
            "message": "Dockerfile has no FROM instruction",
            "why": "Every image must declare a base image.",
            "suggestion": "Add a FROM instruction at the top.",
        })

    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue
        instr = line.split()[0].upper()
        if instr not in VALID_INSTRUCTIONS:
            results.append({
                "level": "improve",
                "symbol": "⚠️",
                "message": f"Unknown Docker instruction: {instr}",
                "why": "Dockerfiles use a fixed set of instructions.",
                "suggestion": "Check spelling or instruction validity.",
            })
            break
    else:
        results.append({
            "level": "ok",
            "symbol": "✅",
            "message": "Dockerfile syntax looks valid",
        })

    return results
