# src/devopsmind/safety/safe_program_shell.py

import os
import tempfile
import json
from pathlib import Path

CONTAINER_WS_ROOT = Path("/workspace")


def launch_program_safe_shell(
    *,
    program_name: str,
    workspace: Path,
    session_id: str,
    container_name: str,
    safety_overrides: dict | None = None,
) -> None:
    """
    DevOpsMind Program Safe Shell

    Rules:
    - `exit` command is blocked (educational)
    - Ctrl+D exits the shell
    - Ctrl+D ALWAYS cleans up container + session
    - Auto-exits on program submit
    """

    workspace = workspace.resolve()
    safety_overrides = safety_overrides or {}

    if safety_overrides:
        (workspace / ".devopsmind_safety_overrides.json").write_text(
            json.dumps(safety_overrides, indent=2)
        )

    devopsmind_root = Path(__file__).resolve().parents[2]

    rcfile = f"""
# =========================================================
# DevOpsMind Program Safe Shell
# Program: {program_name}
# =========================================================

# Ensure Ctrl+D exits
set +o ignoreeof

export DEVOPSMIND_SAFE=1
export DEVOPSMIND_MODE="program"

export DEVOPSMIND_PROGRAM="{program_name}"
export DEVOPSMIND_SESSION="{session_id}"
export DEVOPSMIND_CONTAINER="{container_name}"

export DEVOPSMIND_WS_HOST="{workspace}"
export DEVOPSMIND_WS_CONTAINER="{CONTAINER_WS_ROOT}"

export DEVOPSMIND_ROOT="{devopsmind_root}"
export PYTHONPATH="$DEVOPSMIND_ROOT:$PYTHONPATH"

cd "$DEVOPSMIND_WS_HOST" || exit 1

# ---------------------------------------------------------
# 🧾 Git safety defaults
# ---------------------------------------------------------
git config --local user.name "DevOpsMind User" 2>/dev/null
git config --local user.email "devopsmind@local" 2>/dev/null

export EDITOR="${{EDITOR:-vi}}"
export GIT_EDITOR="$EDITOR"
export GIT_ALLOW_PROTOCOL="file"
unset GIT_EXEC_PATH

# ---------------------------------------------------------
# 🔐 Load command policy
# ---------------------------------------------------------
POLICY_FILE="$DEVOPSMIND_WS_HOST/.devopsmind_safety_overrides.json"

DEVOPSMIND_ALLOWED=""
DEVOPSMIND_BLOCKED=""

if [ -f "$POLICY_FILE" ]; then
    DEVOPSMIND_ALLOWED="$(jq -r '.allowed_commands[]?' "$POLICY_FILE" 2>/dev/null)"
    DEVOPSMIND_BLOCKED="$(jq -r '.blocked_commands[]?' "$POLICY_FILE" 2>/dev/null)"
fi

# ---------------------------------------------------------
# 🔒 Lock user inside workspace
# ---------------------------------------------------------
cd() {{
    builtin cd "$@" || return
    case "$(pwd -P)" in
        "$DEVOPSMIND_WS_HOST"|"$DEVOPSMIND_WS_HOST"/*) ;;
        *)
            echo "✖ You cannot leave the program workspace"
            builtin cd "$DEVOPSMIND_WS_HOST"
            ;;
    esac
}}

# ---------------------------------------------------------
# 🧠 DevOpsMind CLI (PROGRAM AWARE)
# ---------------------------------------------------------
devopsmind() {{
    if [ "$1" = "program" ] && [ -n "$DEVOPSMIND_PROGRAM" ]; then
        if [ -n "$2" ] && [ -z "$3" ]; then
            python3 -m devopsmind program "$2" "$DEVOPSMIND_PROGRAM"
            return $?
        fi
    fi
    python3 -m devopsmind "$@"
}}

# ---------------------------------------------------------
# ⌨️ Autocomplete (user-owned)
# ---------------------------------------------------------
if [ -n "$BASH_VERSION" ]; then
    [ -f "$HOME/.devopsmind/devopsmind.bash" ] && source "$HOME/.devopsmind/devopsmind.bash"
fi

if [ -n "$ZSH_VERSION" ]; then
    [ -f "$HOME/.devopsmind/devopsmind.zsh" ] && source "$HOME/.devopsmind/devopsmind.zsh"
fi

# ---------------------------------------------------------
# 🐳 Container helpers
# ---------------------------------------------------------
__run_container_raw() {{
    command docker exec -i \
        -e EDITOR="$EDITOR" \
        -e GIT_EDITOR="$GIT_EDITOR" \
        -e GIT_ALLOW_PROTOCOL="$GIT_ALLOW_PROTOCOL" \
        -w "$DEVOPSMIND_WS_CONTAINER" \
        "$DEVOPSMIND_CONTAINER" \
        bash -lc "$*"
}}

__run_container_tty() {{
    command docker exec -it \
        -e EDITOR="$EDITOR" \
        -e GIT_EDITOR="$GIT_EDITOR" \
        -e GIT_ALLOW_PROTOCOL="$GIT_ALLOW_PROTOCOL" \
        -w "$DEVOPSMIND_WS_CONTAINER" \
        "$DEVOPSMIND_CONTAINER" \
        bash -lc "$*"
}}

# ---------------------------------------------------------
# 🔁 Git always runs on host
# ---------------------------------------------------------
git() {{
    export GIT_CONFIG_GLOBAL=/dev/null
    export GIT_CONFIG_SYSTEM=/dev/null
    command git "$@"
}}

# ---------------------------------------------------------
# 🔁 Command router
# ---------------------------------------------------------
__command_router() {{
    local cmd="$1"; shift

    for b in $DEVOPSMIND_BLOCKED; do
        [ "$cmd" = "$b" ] && echo "🚫 '$cmd' is locked" && return 127
    done

    if [ -n "$DEVOPSMIND_ALLOWED" ]; then
        local allowed=false
        for a in $DEVOPSMIND_ALLOWED; do
            [ "$a" = "*" ] || [ "$a" = "$cmd" ] && allowed=true
        done
        [ "$allowed" = false ] && echo "🔒 '$cmd' unlocks later" && return 127
    fi

    if __run_container_raw "command -v $cmd" >/dev/null 2>&1; then
        __run_container_tty "$cmd $*"
    else
        command "$cmd" "$@"
    fi
}}

# ---------------------------------------------------------
# 🚫 Docker command control (safety wrapper)
# ---------------------------------------------------------
docker() {{
    case "$1" in
        inspect|history|version|info|help|ps|images)
            __run_container_raw docker "$@"
            ;;
        *)
            echo "🚫 Docker command '$1' is disabled"
            return 127
            ;;
    esac
}}

# ---------------------------------------------------------
# 🚫 Block exit command
# ---------------------------------------------------------
exit() {{
    echo "🚫 Use Ctrl+D to leave the program shell"
    return 127
}}

# ---------------------------------------------------------
# 🧹 Cleanup (AUTHORITATIVE — bypass wrappers)
# ---------------------------------------------------------
__devopsmind_cleanup() {{
    command docker rm -f "$DEVOPSMIND_CONTAINER" >/dev/null 2>&1
    rm -f "$HOME/.devopsmind/programs/$DEVOPSMIND_PROGRAM/session.json"
}}

trap '__devopsmind_cleanup' EXIT INT TERM HUP

# ---------------------------------------------------------
# 🧠 Watch for program submission
# ---------------------------------------------------------
__watch_submit() {{
    if [ -f "$DEVOPSMIND_WS_HOST/.devopsmind_program_completed" ]; then
        echo ""
        echo "🏁 Program completed."
        echo "🧹 Cleaning up and exiting…"
        rm -f "$DEVOPSMIND_WS_HOST/.devopsmind_program_completed"
        builtin exit 0
    fi
}}

if [ -n "$BASH_VERSION" ]; then
    PROMPT_COMMAND="__watch_submit"
fi

if [ -n "$ZSH_VERSION" ]; then
    precmd() {{ __watch_submit; }}
fi

# ---------------------------------------------------------
# 🎨 Prompt (ORIGINAL, STABLE)
# ---------------------------------------------------------
COLOR_BLUE="\\[\\033[38;5;39m\\]"
COLOR_RESET="\\[\\033[0m\\]"

PS1="${{COLOR_BLUE}}devopsmind@{program_name}:~>${{COLOR_RESET}} "

command_not_found_handle() {{
    __command_router "$@"
}}
"""

    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(rcfile)
        rcfile_path = f.name

    shell = os.environ.get("SHELL", "/bin/bash")
    os.execvp(shell, [shell, "--noprofile", "--rcfile", rcfile_path, "-i"])
