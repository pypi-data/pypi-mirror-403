import os

def validate():
    if not os.path.exists("answer.txt"):
        return False, "answer.txt not found."

    content = open("answer.txt").read().lower()

    required_values = ["error", "10:02", "db-primary"]
    required_structure = ["first error", "associated"]

    for value in required_values:
        if value not in content:
            return False, f"Missing required detail: {value}"

    for phrase in required_structure:
        if phrase not in content:
            return False, "Answer does not follow the guided format."

    return True, "Basic log reading correct."
