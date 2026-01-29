import os
import re

def validate():
    if not os.path.exists("Dockerfile"):
        return False, "Dockerfile missing."

    with open("Dockerfile") as f:
        content = f.read()

    # Multi-stage enforcement
    if content.count("FROM") < 2:
        return False, "Dockerfile must use a multi-stage build."

    # Builder stage must install dependencies
    if not re.search(r"RUN\s+pip(3)?\s+install", content):
        return False, "Builder stage must install dependencies."

    # Final stage isolation
    final_stage = content.split("FROM")[-1]

    if "requirements.txt" in final_stage:
        return False, "Final stage must not include requirements.txt."

    # Non-root user enforcement
    if not re.search(r"(adduser|useradd)", final_stage):
        return False, "Final stage must create a non-root user."

    if not re.search(r"USER\s+\w+", final_stage):
        return False, "Final stage must switch to a non-root USER."

    # Runtime command
    if not re.search(r"(CMD|ENTRYPOINT).*python.*app\.py", final_stage):
        return False, "Final stage must run python app.py."

    return True, "Secure multi-stage Dockerfile validated successfully."
