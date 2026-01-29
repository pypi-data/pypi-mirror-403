import os
import re

def validate():
    if not os.path.exists("Dockerfile"):
        return False, "Dockerfile missing."

    with open("Dockerfile") as f:
        content = f.read()

    # Base image must be explicit and slim
    if "FROM python:3.10-slim" not in content:
        return False, "Base image must be python:3.10-slim."

    if re.search(r"FROM\s+python:latest", content):
        return False, "Use of 'latest' tag is not allowed."

    # Working directory
    if not re.search(r"WORKDIR\s+/app", content):
        return False, "WORKDIR /app must be defined."

    # Copy only app.py
    if not re.search(r"COPY\s+app\.py\s+/app", content):
        return False, "Dockerfile must COPY only app.py into /app."

    if re.search(r"COPY\s+\.\s+\.", content):
        return False, "COPY . . is not allowed."

    # Runtime command
    if not re.search(r'CMD\s+\["python",\s*"app\.py"\]', content):
        return False, "CMD must run python app.py."

    return True, "Optimized Dockerfile validated successfully."
