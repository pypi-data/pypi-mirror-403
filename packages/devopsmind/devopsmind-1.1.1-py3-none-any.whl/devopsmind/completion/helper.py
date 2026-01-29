import sys


def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else ""

    try:
        # 🔹 Top-level commands
        if kind == "commands":
            from devopsmind.completion.registry import CLI_REGISTRY
            for cmd in CLI_REGISTRY.keys():
                print(cmd)

        # 🔹 Subcommands (registry-driven)
        elif kind.startswith("subcommands:"):
            command = kind.split(":", 1)[1]
            from devopsmind.completion.registry import CLI_REGISTRY

            entry = CLI_REGISTRY.get(command, {})
            subcommands = entry.get("subcommands", {})

            for sub in subcommands.keys():
                print(sub)

        # 🔹 Lab IDs
        elif kind == "labs":
            from devopsmind.list.lab_resolver import list_all_labs
            for lab in list_all_labs():
                print(lab)

        # 🔹 Stack names
        elif kind == "stacks":
            from devopsmind.list.stacks import list_all_stacks
            for stack in list_all_stacks():
                print(stack)

        # 🔹 Project IDs
        elif kind == "projects":
            from devopsmind.handlers.project.registry import list_owned_project_ids
            for pid in list_owned_project_ids():
                print(pid)

        # 🔹 Program IDs
        elif kind == "programs":
            from devopsmind.programs.loader import list_available_programs
            for program in list_available_programs():
                print(program)

    except Exception:
        # Autocomplete must NEVER break the shell
        pass


if __name__ == "__main__":
    main()
