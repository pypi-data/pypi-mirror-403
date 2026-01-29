CLI_REGISTRY = {
    # onboarding
    "login": {},
    "logout": {},
    "introduce": {},

    # labs
    "start": {"args": ["<id>"]},
    "resume": {"args": ["<id>"]},
    "reset": {"args": ["<id>"]},
    "validate": {"args": ["<id>"]},
    "search": {"args": ["<term>"]},
    "describe": {"args": ["<id>"]},
    "hint": {"args": ["<id>"]},
    "mentor": {},

    # progress
    "stats": {},
    "stacks": {
        "flags": {
            "--corepro": {},
            "--foundation": {},
            "--cloudops": {},
            "--securityops": {},
            "--observability": {},
            "--scenarios": {},
            "--story": {},
            "--linux-admin": {},
            "--python-dev": {},
        }
    },
    "badges": {},

    # profile
    "profile": {
        "subcommands": {
            "show": {}
        }
    },

    # projects (static superset)
    "projects": {},
    "project": {
        "subcommands": {
            "describe": {"args": ["<id>"]},
            "start": {"args": ["<id>"]},
            "resume": {"args": ["<id>"]},
            "status": {"args": ["<id>"]},
            "validate": {"args": ["<id>"]},
            "submit": {"args": ["<id>"]},
        }
    },

    # programs (guided learning tracks)
    "programs": {},
    "program": {
        "args": ["<name>"],
        "subcommands": {
            "cert": {"args": ["<program>"]},
            "validate": {"args": ["<program>"]},
            "simulate": {"args": ["<program>"]},
            "submit": {"args": ["<program>"]},
            "check": {"args": ["<program>"]},
        }
    },

    # utilities
    "doctor": {},
    "sync": {},
    "submit": {},

    # auth & mode
    "auth": {
        "subcommands": {
            "rotate-recovery": {}
        }
    },
    "mode": {
        "subcommands": {
            "online": {},
            "offline": {}
        }
    }
}
