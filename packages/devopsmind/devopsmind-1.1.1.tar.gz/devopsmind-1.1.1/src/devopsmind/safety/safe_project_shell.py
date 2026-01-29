import os
import tempfile
import json
from pathlib import Path

CONTAINER_WS_ROOT = Path("/workspace")


def launch_safe_project_shell(
    workspace: Path,
    project_id: str,
    stack: str,
    session_id: str,
    container_name: str,
    safety_overrides=None,
):
    """
    DevOpsMind Safe Project Shell

    HARD RULES:
    - Project shell NEVER auto-exits on validate
    - Project shell auto-exits ONLY after successful submit
    - Ctrl+D MUST exit and clean up container
    """

    workspace = workspace.resolve()
    safety_overrides = safety_overrides or {}

    if safety_overrides:
        (workspace / ".devopsmind_project_safety_overrides.json").write_text(
            json.dumps(safety_overrides, indent=2)
        )

    devopsmind_root = Path(__file__).resolve().parents[2]

    rcfile = f"""
# =========================================================
# DevOpsMind Safe Project Shell
# =========================================================

export DEVOPSMIND_SAFE=1
export DEVOPSMIND_MODE="project"

export DEVOPSMIND_WS_HOST="{workspace}"
export DEVOPSMIND_WS_CONTAINER="{CONTAINER_WS_ROOT}"

export DEVOPSMIND_PROJECT="{project_id}"
export DEVOPSMIND_STACK="{stack}"
export DEVOPSMIND_SESSION="{session_id}"
export DEVOPSMIND_CONTAINER="{container_name}"

export DEVOPSMIND_ROOT="{devopsmind_root}"
export PYTHONPATH="$DEVOPSMIND_ROOT:$PYTHONPATH"

cd "$DEVOPSMIND_WS_HOST" || exit 1

# ---------------------------------------------------------
# 🔧 Ensure Ctrl+D exits shell (CRITICAL)
# ---------------------------------------------------------
set +o ignoreeof

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
# 🎨 Colors
# ---------------------------------------------------------
COLOR_OCEAN_BLUE="\\[\\033[38;5;39m\\]"
COLOR_RESET="\\[\\033[0m\\]"

export CLICOLOR=1
alias ls='ls --color=auto'

# ---------------------------------------------------------
# 🔒 Lock user inside project workspace
# ---------------------------------------------------------
cd() {{
    builtin cd "$@" || return
    case "$(pwd -P)" in
        "$DEVOPSMIND_WS_HOST"|"$DEVOPSMIND_WS_HOST"/*) ;;
        *)
            echo "✖ You cannot leave the project workspace"
            builtin cd "$DEVOPSMIND_WS_HOST"
            ;;
    esac
}}

# ---------------------------------------------------------
# 🧠 DevOpsMind CLI (PROJECT AWARE)
# ---------------------------------------------------------
devopsmind() {{
    case "$1" in
        project)
            if [ -z "$3" ]; then
                python3 -m devopsmind project "$2" "$DEVOPSMIND_PROJECT"
                return $?
            fi
            ;;
    esac
    python3 -m devopsmind "$@"
}}

# ---------------------------------------------------------
# ⌨️ Autocomplete
# ---------------------------------------------------------
if [ -n "$BASH_VERSION" ]; then
    [ -f "$HOME/.devopsmind/devopsmind.bash" ] && source "$HOME/.devopsmind/devopsmind.bash"
fi

if [ -n "$ZSH_VERSION" ]; then
    [ -f "$HOME/.devopsmind/devopsmind.zsh" ] && source "$HOME/.devopsmind/devopsmind.zsh"
fi

# ---------------------------------------------------------
# 🐳 Container execution helpers
# ---------------------------------------------------------
__run_container_raw() {{
    docker exec -i -w "$DEVOPSMIND_WS_CONTAINER" "$DEVOPSMIND_CONTAINER" bash -lc "$*"
}}

__run_container_tty() {{
    docker exec -it -w "$DEVOPSMIND_WS_CONTAINER" "$DEVOPSMIND_CONTAINER" bash -lc "$*"
}}

# ---------------------------------------------------------
# 🔁 Tool router
# ---------------------------------------------------------
__command_router() {{
    local cmd="$1"
    shift

    case "$cmd" in
        git|devopsmind|cd|exit|docker)
            command "$cmd" "$@"
            ;;
        *)
            if __run_container_raw "command -v $cmd" >/dev/null 2>&1; then
                __run_container_tty "$cmd $*"
            else
                command "$cmd" "$@"
            fi
            ;;
    esac
}}

# ---------------------------------------------------------
# 🚫 Disable exit keyword
# ---------------------------------------------------------
exit() {{
    echo "🚫 Exit is disabled. Use Ctrl+D to leave the project."
    return 127
}}

# ---------------------------------------------------------
# 🧹 Cleanup (AUTHORITATIVE)
# ---------------------------------------------------------
__devopsmind_cleanup() {{
    echo "🧹 Cleaning up project container and volumes..."

    docker rm -f "$DEVOPSMIND_CONTAINER" >/dev/null 2>&1

    docker volume ls -q \
      --filter "label=devopsmind.project=$DEVOPSMIND_PROJECT" \
      | xargs -r docker volume rm >/dev/null 2>&1
}}

# ---------------------------------------------------------
# 🧠 Project lifecycle watcher
# ---------------------------------------------------------
__watch_project_state() {{
    if [ -f "$DEVOPSMIND_WS_HOST/.devopsmind_project_submitted" ]; then
        echo ""
        echo "🏁 Project submitted successfully."
        echo "👋 Exiting project shell."

        __devopsmind_cleanup
        builtin exit 0
    fi
}}

if [ -n "$BASH_VERSION" ]; then
    PROMPT_COMMAND="__watch_project_state"
fi

if [ -n "$ZSH_VERSION" ]; then
    precmd() {{ __watch_project_state; }}
fi

trap '__devopsmind_cleanup' EXIT INT TERM HUP

__devopsmind_pwd() {{
    case "$PWD" in
        "$DEVOPSMIND_WS_HOST") echo "~" ;;
        "$DEVOPSMIND_WS_HOST"/*) echo "~/${{PWD#"$DEVOPSMIND_WS_HOST"/}}" ;;
        *) echo "$PWD" ;;
    esac
}}

PS1="${{COLOR_OCEAN_BLUE}}devopsmind@project:{project_id}:$(__devopsmind_pwd)> ${{COLOR_RESET}}"

command_not_found_handle() {{
    __command_router "$@"
}}
"""

    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(rcfile)
        rcfile_path = f.name

    shell = os.environ.get("SHELL", "/bin/bash")
    os.execvp(shell, [shell, "--noprofile", "--rcfile", rcfile_path, "-i"])
