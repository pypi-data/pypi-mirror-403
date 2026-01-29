"""
Outbox trigger
Fire-and-forget background processor
"""

import subprocess
import sys
from pathlib import Path


def trigger_outbox_processor(program_dir: Path):
    """
    Starts the outbox processor in background.
    Must NEVER block or fail submission.
    Always runs in host context.
    """
    try:
        subprocess.Popen(
            [
                "devopsmind-outbox",
                str(program_dir),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass
