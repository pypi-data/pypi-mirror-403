import json
import urllib.request

VERSION_URL = (
    "https://raw.githubusercontent.com/"
    "InfraForgeLabs/infraforgelabs.github.io/main/meta/devopsmind/version.json"
)

RUNTIME_IMAGE_REPO = "infraforgelabs/devopsmind-runtime"


def fetch_runtime_version() -> str | None:
    try:
        with urllib.request.urlopen(VERSION_URL, timeout=5) as resp:
            data = json.load(resp)
        return str(data.get("runtime_version")).strip()
    except Exception:
        return None


def required_runtime_image() -> str | None:
    version = fetch_runtime_version()
    if not version:
        return None
    return f"{RUNTIME_IMAGE_REPO}:{version}"
