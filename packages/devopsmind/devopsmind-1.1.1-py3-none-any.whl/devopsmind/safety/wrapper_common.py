import sys
import subprocess
from devopsmind.safety.stack_policy import GLOBAL_BLOCKS, STACK_BLOCKS


def run_wrapper(tool: str, real_binary: str):
    args = sys.argv[1:]
    cmd_str = " ".join(args)

    # Global destructive blocks
    for g in GLOBAL_BLOCKS:
        if g in cmd_str:
            print("✖ Blocked destructive system command")
            sys.exit(1)

    # Stack-specific destructive blocks
    for b in STACK_BLOCKS.get(tool, []):
        if b in cmd_str:
            print(f"✖ Blocked destructive {tool} command")
            sys.exit(1)

    subprocess.run([real_binary] + args, check=False)
