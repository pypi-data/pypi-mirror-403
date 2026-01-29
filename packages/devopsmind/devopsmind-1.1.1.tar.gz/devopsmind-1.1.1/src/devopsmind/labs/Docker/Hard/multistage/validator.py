import os
import re

def validate():
    if not os.path.exists("Dockerfile"):
        return False, "Dockerfile missing."

    if not os.path.exists("app.py"):
        return False, "app.py required."

    if not os.path.exists("requirements.txt"):
        return False, "requirements.txt required."

    with open("Dockerfile") as f:
        content = f.read()

    # Multi-stage requirement
    if content.count("FROM") < 2:
        return False, "Dockerfile must use multi-stage build (at least two FROM statements)."

    # Builder stage must install dependencies
    if not re.search(r"RUN\s+pip(3)?\s+install", content):
        return False, "Builder stage must install dependencies using pip."

    # requirements.txt must not be copied into final stage
    final_stage = content.split("FROM")[-1]
    if "requirements.txt" in final_stage:
        return False, "Final stage must not include requirements.txt."

    # Final stage must run python app.py
    if not re.search(r"(CMD|ENTRYPOINT).*python.*app\.py", content):
        return False, "Final stage must run python app.py."

    return True, "Multi-stage Dockerfile validated successfully."
