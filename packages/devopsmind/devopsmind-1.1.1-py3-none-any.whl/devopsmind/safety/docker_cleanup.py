import subprocess


def cleanup_lab_containers(lab_id: str):
    result = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        stdout=subprocess.PIPE,
        text=True,
    )

    for name in result.stdout.splitlines():
        if name.startswith(f"devopsmind-lab-{lab_id}-"):
            subprocess.run(
                ["docker", "rm", "-f", name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
