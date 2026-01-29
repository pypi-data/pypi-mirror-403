import subprocess
from devopsmind.runtime.docker.registry import SERVICES


def up(services: list[str]):
    for svc in services:
        compose = SERVICES[svc]["compose"]
        subprocess.run(
            ["docker", "compose", "-f", compose, "up", "-d"],
            check=True
        )


def down(services: list[str]):
    for svc in services:
        compose = SERVICES[svc]["compose"]
        subprocess.run(
            ["docker", "compose", "-f", compose, "down", "-v"],
            check=False
        )
