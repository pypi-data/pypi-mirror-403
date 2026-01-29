# devopsmind/runtime/__init__.py

"""
DevOpsMind runtime package.

Contains Docker runtime configuration, defaults,
and execution environment flags.
"""

import os

# -------------------------------------------------
# Runtime identity flag
# -------------------------------------------------
# True  -> running inside DevOpsMind Docker runtime
# False -> running on host (CLI, UX, setup)
#
# Set inside Docker image via ENV.
# -------------------------------------------------
IS_INTERNAL = os.environ.get("DEVOPSMIND_INTERNAL", "0") == "1"
