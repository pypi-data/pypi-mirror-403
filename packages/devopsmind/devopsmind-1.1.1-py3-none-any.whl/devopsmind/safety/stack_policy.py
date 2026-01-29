"""
DevOpsMind Safety Policy Engine
"""

from typing import Tuple


# --------------------------------------------------
# 🚨 Global hard blocks
# --------------------------------------------------
GLOBAL_BLOCKS = [
    ("rm", ["-rf", "--no-preserve-root"]),
    ("sudo", None),
    ("shutdown", None),
    ("reboot", None),
    ("poweroff", None),
    ("mkfs", None),
    ("dd", None),
]


# --------------------------------------------------
# ⚙️ Stack-specific blocks
# --------------------------------------------------
STACK_BLOCKS = {
    "terraform": [
        ("terraform", ["apply", "destroy", "import"]),
    ],
    "kubectl": [
        ("kubectl", [
            "delete node",
            "delete ns kube-system",
            "delete namespace kube-system",
            "drain",
            "cordon",
            "taint node",
        ]),
    ],
    "aws": [
        ("aws", [
            "terminate-instances",
            "delete-stack",
            "rb",
            "delete",
        ]),
    ],
    "helm": [
        ("helm", ["uninstall", "rollback"]),
    ],
}


# --------------------------------------------------
# 🐳 Docker strict allow-only mode
# --------------------------------------------------
DOCKER_ALLOWED = [
    "docker build",
    "docker rm",
    "docker stop",
    "docker rmi",
    "docker ps",
]


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def _tokenize(command: str) -> list[str]:
    return command.strip().split()


def _matches(tokens: list[str], base: str, patterns: list[str] | None) -> bool:
    if not tokens or tokens[0] != base:
        return False

    if patterns is None:
        return True

    rest = " ".join(tokens[1:])
    return any(p in rest for p in patterns)


# --------------------------------------------------
# Core safety check
# --------------------------------------------------
def is_command_blocked(command: str, stack: str | None) -> Tuple[bool, str]:
    tokens = _tokenize(command)
    if not tokens:
        return False, ""

    for base, patterns in GLOBAL_BLOCKS:
        if _matches(tokens, base, patterns):
            return True, f"Global safety rule: '{base}' is not allowed"

    if stack == "docker":
        if len(tokens) < 2:
            return True, "docker safety rule: incomplete docker command"

        cmd = " ".join(tokens[:2])
        if cmd not in DOCKER_ALLOWED:
            return True, (
                "docker safety rule: only the following commands are allowed: "
                f"{DOCKER_ALLOWED}"
            )
        return False, ""

    if stack and stack in STACK_BLOCKS:
        for base, patterns in STACK_BLOCKS[stack]:
            if _matches(tokens, base, patterns):
                return True, f"{stack} safety rule: destructive command blocked"

    return False, ""


# --------------------------------------------------
# Per-lab overrides
# --------------------------------------------------
def apply_lab_overrides(command: str, overrides: dict | None):
    if not overrides:
        return False, ""

    cmd = command.strip()

    for rule in overrides.get("block", []):
        if rule in cmd:
            return True, f"Lab rule: '{rule}' is blocked"

    if overrides.get("allow_only"):
        allowed = overrides.get("allow", [])
        if not any(cmd.startswith(a) for a in allowed):
            return True, f"Lab rule: only {allowed} allowed"

    return False, ""
