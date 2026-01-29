from pathlib import Path

# =================================================
# Completion version (AUTHORITATIVE)
# =================================================
COMPLETION_VERSION = 1


# =================================================
# Bash completion
# =================================================

def _generate_bash():
    return f"""\
# DEVOPSMIND_COMPLETION_VERSION={COMPLETION_VERSION}

_devopsmind() {{
    local cur prev
    COMPREPLY=()

    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"

    # 🔹 Top-level commands
    if [[ $COMP_CWORD -eq 1 ]]; then
        COMPREPLY=(
            $(compgen -W "$(devopsmind-complete commands 2>/dev/null)" -- "$cur")
        )
        return
    fi

    # 🔹 Lab ID completion
    if [[ "$prev" =~ ^(start|resume|reset|validate|describe|hint)$ ]]; then
        COMPREPLY=(
            $(compgen -W "$(devopsmind-complete labs 2>/dev/null)" -- "$cur")
        )
        return
    fi

    # 🔹 Stack name completion (search)
    if [[ "$prev" == "search" ]]; then
        COMPREPLY=(
            $(compgen -W "$(devopsmind-complete stacks 2>/dev/null)" -- "$cur")
        )
        return
    fi

    # 🔹 Mode subcommands
    if [[ "$prev" == "mode" ]]; then
        COMPREPLY=(
            $(compgen -W "$(devopsmind-complete subcommands:mode 2>/dev/null)" -- "$cur")
        )
        return
    fi

    # 🔹 Auth subcommands
    if [[ "$prev" == "auth" ]]; then
        COMPREPLY=(
            $(compgen -W "$(devopsmind-complete subcommands:auth 2>/dev/null)" -- "$cur")
        )
        return
    fi

    # 🔹 Profile subcommands
    if [[ "$prev" == "profile" ]]; then
        COMPREPLY=(
            $(compgen -W "$(devopsmind-complete subcommands:profile 2>/dev/null)" -- "$cur")
        )
        return
    fi

    # 🔹 Project subcommands
    if [[ "$prev" == "project" ]]; then
        COMPREPLY=(
            $(compgen -W "$(devopsmind-complete subcommands:project 2>/dev/null)" -- "$cur")
        )
        return
    fi

    # 🔹 Project ID completion
    if [[ "${{COMP_WORDS[1]}}" == "project" && $COMP_CWORD -eq 3 ]]; then
        COMPREPLY=(
            $(compgen -W "$(devopsmind-complete projects 2>/dev/null)" -- "$cur")
        )
        return
    fi

    # 🔹 Program subcommands
    if [[ "$prev" == "program" ]]; then
        COMPREPLY=(
            $(compgen -W "$(devopsmind-complete subcommands:program 2>/dev/null)" -- "$cur")
        )
        return
    fi

    # 🔹 Program names
    if [[ "${{COMP_WORDS[1]}}" == "program" && $COMP_CWORD -ge 3 ]]; then
        COMPREPLY=(
            $(compgen -W "$(devopsmind-complete programs 2>/dev/null)" -- "$cur")
        )
        return
    fi
}}

complete -F _devopsmind devopsmind
"""


# =================================================
# Zsh completion
# =================================================

def _generate_zsh():
    return f"""\
#compdef devopsmind
# DEVOPSMIND_COMPLETION_VERSION={COMPLETION_VERSION}

_devopsmind() {{
    local -a commands
    local prev

    commands=( ${{{{(f)"$(devopsmind-complete commands 2>/dev/null)"}}}} )
    prev="${{{{words[$CURRENT-1]}}}}"

    # 🔹 Top-level commands
    if (( CURRENT == 2 )); then
        _describe 'command' commands
        return
    fi

    # 🔹 Lab completion
    if [[ "$prev" =~ ^(start|resume|reset|validate|describe|hint)$ ]]; then
        _values 'labs' ${{{{(f)"$(devopsmind-complete labs 2>/dev/null)"}}}}
        return
    fi

    # 🔹 Stack completion (search)
    if [[ "$prev" == "search" ]]; then
        _values 'stacks' ${{{{(f)"$(devopsmind-complete stacks 2>/dev/null)"}}}}
        return
    fi

    # 🔹 Mode subcommands
    if [[ "$prev" == "mode" ]]; then
        _values 'mode action' ${{{{(f)"$(devopsmind-complete subcommands:mode 2>/dev/null)"}}}}
        return
    fi

    # 🔹 Auth
    if [[ "$prev" == "auth" ]]; then
        _values 'auth action' ${{{{(f)"$(devopsmind-complete subcommands:auth 2>/dev/null)"}}}}
        return
    fi

    # 🔹 Profile
    if [[ "$prev" == "profile" ]]; then
        _values 'profile action' ${{{{(f)"$(devopsmind-complete subcommands:profile 2>/dev/null)"}}}}
        return
    fi

    # 🔹 Project actions
    if [[ "$prev" == "project" ]]; then
        _values 'project action' ${{{{(f)"$(devopsmind-complete subcommands:project 2>/dev/null)"}}}}
        return
    fi

    # 🔹 Project IDs
    if [[ "${{{{words[2]}}}}" == "project" && CURRENT == 4 ]]; then
        _values 'project id' ${{{{(f)"$(devopsmind-complete projects 2>/dev/null)"}}}}
        return
    fi

    # 🔹 Program actions
    if [[ "$prev" == "program" ]]; then
        _values 'program action' ${{{{(f)"$(devopsmind-complete subcommands:program 2>/dev/null)"}}}}
        return
    fi

    # 🔹 Program names
    if [[ "${{{{words[2]}}}}" == "program" && CURRENT >= 4 ]]; then
        _values 'program' ${{{{(f)"$(devopsmind-complete programs 2>/dev/null)"}}}}
        return
    fi
}}

_devopsmind "$@"
"""


# =================================================
# Public API
# =================================================

def generate_all(target_dir: Path):
    target_dir.mkdir(parents=True, exist_ok=True)

    (target_dir / "devopsmind.bash").write_text(_generate_bash())
    (target_dir / "devopsmind.zsh").write_text(_generate_zsh())
