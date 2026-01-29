import os
import tempfile
import json
from pathlib import Path

CONTAINER_WS_ROOT = Path("/workspace")


def launch_safe_shell(
    workspace: Path,
    lab_id: str,
    stack: str,
    session_id: str,
    container_name: str,
    safety_overrides=None,
):
    workspace = workspace.resolve()
    safety_overrides = safety_overrides or {}

    if safety_overrides:
        (workspace / ".devopsmind_safety_overrides.json").write_text(
            json.dumps(safety_overrides)
        )

    devopsmind_root = Path(__file__).resolve().parents[2]

    rcfile = f"""
# =========================================================
# DevOpsMind Safe Shell
# =========================================================

export DEVOPSMIND_SAFE=1
export DEVOPSMIND_WS_HOST="{workspace}"
export DEVOPSMIND_WS_CONTAINER="{CONTAINER_WS_ROOT}"
export DEVOPSMIND_CHALLENGE="{lab_id}"
export DEVOPSMIND_STACK="{stack}"
export DEVOPSMIND_SESSION="{session_id}"
export DEVOPSMIND_CONTAINER="{container_name}"

export DEVOPSMIND_ROOT="{devopsmind_root}"
export PYTHONPATH="$DEVOPSMIND_ROOT:$PYTHONPATH"

cd "$DEVOPSMIND_WS_HOST" || exit 1

# ---------------------------------------------------------
# 🧾 ADDITIVE FIXES ONLY
# ---------------------------------------------------------
git config --local user.name "DevOpsMind User" 2>/dev/null
git config --local user.email "devopsmind@local" 2>/dev/null

export EDITOR="${{EDITOR:-vi}}"
export GIT_EDITOR="$EDITOR"
export GIT_ALLOW_PROTOCOL="file"

# ---------------------------------------------------------
# 🧼 Ensure Git uses built-in exec-path
# ---------------------------------------------------------
unset GIT_EXEC_PATH

# ---------------------------------------------------------
# 🎨 Colors & LS theming
# ---------------------------------------------------------
COLOR_OCEAN_BLUE="\\[\\033[38;5;39m\\]"
COLOR_RESET="\\[\\033[0m\\]"

export CLICOLOR=1
export LSCOLORS=ExFxBxDxCxegedabagacad
alias ls='ls --color=auto'

# ---------------------------------------------------------
# 🔒 Lock user inside workspace
# ---------------------------------------------------------
cd() {{
    builtin cd "$@" || return
    case "$(pwd -P)" in
        "$DEVOPSMIND_WS_HOST"|"$DEVOPSMIND_WS_HOST"/*) ;;
        *)
            echo "✖ You cannot leave the lab workspace"
            builtin cd "$DEVOPSMIND_WS_HOST"
            ;;
    esac
}}

# ---------------------------------------------------------
# 🧠 DevOpsMind CLI (HOST ONLY)
# ---------------------------------------------------------
devopsmind() {{
    case "$1" in
        describe|hint|validate)
            if [ -z "$2" ]; then
                python3 -m devopsmind "$1" "$DEVOPSMIND_CHALLENGE"
                return $?
            fi
            ;;
    esac
    python3 -m devopsmind "$@"
}}

# ---------------------------------------------------------
# ⌨️ Autocomplete (User-owned files)
# ---------------------------------------------------------
if [ -n "$BASH_VERSION" ]; then
    if [ -f "$HOME/.devopsmind/devopsmind.bash" ]; then
        source "$HOME/.devopsmind/devopsmind.bash"
    fi
fi

if [ -n "$ZSH_VERSION" ]; then
    if [ -f "$HOME/.devopsmind/devopsmind.zsh" ]; then
        source "$HOME/.devopsmind/devopsmind.zsh"
    fi
fi

# ---------------------------------------------------------
# 🐳 Container execution helpers
# ---------------------------------------------------------
__run_container_raw() {{
    command docker exec -i \
        -e GIT_EDITOR="$GIT_EDITOR" \
        -e EDITOR="$EDITOR" \
        -e GIT_ALLOW_PROTOCOL="$GIT_ALLOW_PROTOCOL" \
        -w "$DEVOPSMIND_WS_CONTAINER" \
        "$DEVOPSMIND_CONTAINER" \
        bash -lc "$*"
}}

__run_container_tty() {{
    command docker exec -it \
        -e GIT_EDITOR="$GIT_EDITOR" \
        -e EDITOR="$EDITOR" \
        -e GIT_ALLOW_PROTOCOL="$GIT_ALLOW_PROTOCOL" \
        -w "$DEVOPSMIND_WS_CONTAINER" \
        "$DEVOPSMIND_CONTAINER" \
        bash -lc "$*"
}}

# ---------------------------------------------------------
# 🔁 Git runs on HOST (sandboxed)
# ---------------------------------------------------------
git() {{
    export GIT_CONFIG_GLOBAL=/dev/null
    export GIT_CONFIG_SYSTEM=/dev/null
    command git "$@"
}}

# ---------------------------------------------------------
# 🔁 Tool router (container-first, git excluded)
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
# 🚫 Docker command CONTROL (SAFE ALLOWLIST)
# ---------------------------------------------------------
docker() {{
    case "$1" in
        build|buildx)
            shift
            echo "🛠️  Building image using DevOpsMind BuildKit…"
            buildctl build \
              --frontend dockerfile.v0 \
              --local context=. \
              --local dockerfile=. \
              --output type=image,name=devopsmind-temp,oci-mediatypes=true \
              --addr tcp://host.docker.internal:1234
            return $?
            ;;

        compose)
            shift
            __run_container_tty docker compose "$@"
            return $?
            ;;

        inspect|history|manifest|version|info|help|ps|images)
            __run_container_raw docker "$@"
            return $?
            ;;

        *)
            echo "🚫 Docker command '$1' is disabled in DevOpsMind"
            return 127
            ;;
    esac
}}

# ---------------------------------------------------------
# 🚫 BLOCK exit
# ---------------------------------------------------------
exit() {{
    echo "🚫 Exit is disabled. Use Ctrl+D to leave the lab."
    return 127
}}

# ---------------------------------------------------------
# 🧹 Cleanup
# ---------------------------------------------------------
__devopsmind_cleanup() {{
    command docker rm -f "$DEVOPSMIND_CONTAINER" >/dev/null 2>&1
}}

__watch_success() {{
    if [ -f "$DEVOPSMIND_WS_HOST/.devopsmind_success" ]; then
        __devopsmind_cleanup
        rm -rf "$DEVOPSMIND_WS_HOST"
        builtin exit 0
    fi
}}

if [ -n "$BASH_VERSION" ]; then
    PROMPT_COMMAND="__watch_success"
fi

if [ -n "$ZSH_VERSION" ]; then
    precmd() {{
        __watch_success
    }}
fi

trap '__devopsmind_cleanup' EXIT
trap '__devopsmind_cleanup' INT TERM HUP

__devopsmind_pwd() {{
    case "$PWD" in
        "$DEVOPSMIND_WS_HOST") echo "~" ;;
        "$DEVOPSMIND_WS_HOST"/*) echo "~/${{PWD#"$DEVOPSMIND_WS_HOST"/}}" ;;
        *) echo "$PWD" ;;
    esac
}}

PS1="${{COLOR_OCEAN_BLUE}}devopsmind@{lab_id}:$(__devopsmind_pwd)> ${{COLOR_RESET}}"

# ---------------------------------------------------------
# 🔁 Final command hook
# ---------------------------------------------------------
command_not_found_handle() {{
    __command_router "$@"
}}
"""

    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(rcfile)
        rcfile_path = f.name

    shell = os.environ.get("SHELL", "/bin/bash")
    os.execvp(shell, [shell, "--noprofile", "--rcfile", rcfile_path, "-i"])
