# devopsmind/runtime/docker_defaults.py

"""
Authoritative Docker service defaults.

HARD RULE:
- All labs run inside Docker
- If a lab does not declare services,
  a default service is derived from its stack
"""

DEFAULT_DOCKER_SERVICE = {
    "ansible": "ansible",
    "terraform": "terraform",
    "kubernetes": "k8s",
    "git": "git",
    "linux": "linux",
    "security": "security",
}

# Fallback if stack is unknown
FALLBACK_SERVICE = "base"
