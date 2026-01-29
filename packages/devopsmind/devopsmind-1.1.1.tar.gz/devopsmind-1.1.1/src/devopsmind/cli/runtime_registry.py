from devopsmind.handlers.stacks_handler import handle_stacks
from devopsmind.handlers.validate_handler import handle_validate

RUNTIME_REGISTRY = {
    "stacks": {
        "handler": handle_stacks,
        "flag_map": {
            "--corepro": "--corepro",
            "--foundation": "--corepro",
            "--cloudops": "--cloudops",
            "--securityops": "--securityops",
            "--observability": "--observability",
            "--scenarios": "--scenarios",
            "--story": "--story",
            "--linux-admin": "--linux-admin",
            "--python-dev": "--python-dev",
        },
    },
    "validate": {
        "handler": handle_validate,
    },
}
