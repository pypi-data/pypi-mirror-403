"""
Internal outbox sync command

⚠️ NOT user-facing
⚠️ Used only by background trigger
"""

from pathlib import Path
import sys

from devopsmind.programs.outbox.processor import process_outbox


def main():
    print("[OUTBOX CLI] started")

    if len(sys.argv) < 2:
        print("[OUTBOX CLI] missing program_dir argument")
        sys.exit(1)

    program_dir = Path(sys.argv[1]).expanduser().resolve()
    print("[OUTBOX CLI] program_dir:", program_dir)

    if not program_dir.exists():
        print("[OUTBOX CLI] program_dir does not exist")
        sys.exit(1)

    print("[OUTBOX CLI] invoking processor")
    process_outbox(program_dir)
    print("[OUTBOX CLI] done")


if __name__ == "__main__":
    main()
