import os
import re

def validate():
    if not os.path.exists("Dockerfile"):
        return False, "Dockerfile missing."

    if not os.path.exists("app.py"):
        return False, "app.py missing (required)."

    with open("Dockerfile") as f:
        content = f.read().strip()

    if "FROM python:3.10-alpine" not in content:
        return False, "Dockerfile must use base image python:3.10-alpine."

    if not re.search(r"COPY\s+app\.py\s+/app/app\.py", content):
        return False, "Dockerfile must copy app.py to /app/app.py."

    if "WORKDIR /app" not in content:
        return False, "Dockerfile must set WORKDIR to /app."

    if not re.search(r'CMD\s+\["python3",\s*"app\.py"\]', content):
        return False, 'Dockerfile must run CMD ["python3", "app.py"].'

    return True, "Dockerfile structure looks correct."
