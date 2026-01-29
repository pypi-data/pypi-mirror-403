# src/devopsmind/programs/dashboard.py

from devopsmind.programs.state import load_program_state
from devopsmind.programs.progress import load_progress


DOTS = 5


def _coverage_to_dots(percent: int) -> list[bool]:
    """
    Convert percentage into filled dot slots.
    """
    filled = round((percent / 100) * DOTS)
    return [i < filled for i in range(DOTS)]


def get_dashboard_view(program: str) -> list[dict]:
    """
    Returns dashboard-ready data per system.
    """
    state = load_program_state(program)
    progress = load_progress(program)

    view = []

    for system in ["execution", "resilience", "delivery"]:
        percent = progress["systems"].get(system, 0)
        dots = _coverage_to_dots(percent)

        view.append({
            "system": system.capitalize(),
            "state": state["systems"].get(system, "LOCKED"),
            "coverage": percent,
            "dots": dots,
        })

    return view
