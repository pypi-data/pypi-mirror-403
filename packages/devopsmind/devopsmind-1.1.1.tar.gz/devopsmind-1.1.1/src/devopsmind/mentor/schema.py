# devopsmind/mentor/schema.py

from typing import TypedDict, List, Literal, Dict, Optional


MentorLevel = Literal["Beginner", "Intermediate", "Advanced"]


class MentorAdvice(TypedDict, total=False):
    # ---------------- EXISTING (unchanged) ----------------
    level: MentorLevel
    summary: str
    next_lab: Dict[str, str]
    why: str
    insight: str
    after_that: List[str]

    # ---------------- NEW (ADDITIVE) ----------------
    recommendations: List[Dict[str, str]]
    confidence: Dict[str, Dict[str, int | str]]

    learning_style: Dict[str, str]
    cadence: str

    # Derived / explanatory (no hardcoding)
    lab_reasons: Dict[str, str]
    stack_balance: str
    focus_horizon: str
    style_action: str
    stretch_lab: Optional[Dict[str, str]]
