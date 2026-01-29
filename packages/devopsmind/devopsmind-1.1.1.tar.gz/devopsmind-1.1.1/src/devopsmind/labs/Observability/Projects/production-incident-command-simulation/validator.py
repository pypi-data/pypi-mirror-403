import os

REQUIRED_FILES = {
    "incident-brief.md": [
        "context",
        "initial assessment",
        "scope of impact",
        "immediate concerns",
        "ownership",
    ],
    "decision-log.md": [
        "decision context",
        "containment actions",
        "escalation decisions",
        "risk ownership",
    ],
    "communication-brief.md": [
        "audience",
        "communication decision",
        "message scope",
        "approval flow",
        "ownership",
    ],
    "post-incident-review.md": [
        "incident summary",
        "accountability assessment",
        "organizational learning",
        "irreversible decisions",
        "culture and trust impact",
        "ownership",
    ],
}

# Instructional sentence starters only (not normal prose)
PLACEHOLDER_STARTS = [
    "describe ",
    "state ",
    "identify ",
    "summarize ",
    "document ",
    "explain ",
    "define ",
]


def extract_section(content: str, section_title: str) -> str | None:
    """
    Extract the body text under a markdown '## Section'.
    Returns None if section is missing or empty.
    """
    lines = content.splitlines()
    section_title = section_title.lower()

    capturing = False
    body = []

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        if lower.startswith("## ") and section_title in lower:
            capturing = True
            continue

        if capturing:
            if lower.startswith("## "):
                break
            if stripped:
                body.append(stripped)

    text = "\n".join(body).strip()
    return text if text else None


def is_placeholder(text: str) -> bool:
    """
    Detect template / instructional text without flagging real prose.
    """
    text = text.strip().lower()

    # Untouched template block like "(Describe ...)"
    if text.startswith("(") and text.endswith(")"):
        return True

    # Instructional sentences only if they START the section
    return any(text.startswith(p) for p in PLACEHOLDER_STARTS)


def validate():
    combined_authored_text = ""

    for file, sections in REQUIRED_FILES.items():
        if not os.path.exists(file):
            return False, f"Missing required deliverable: {file}"

        raw = open(file).read()

        for section in sections:
            body = extract_section(raw, section)

            if not body:
                return False, f"Missing section '{section.title()}' in {file}"

            if is_placeholder(body):
                return (
                    False,
                    f"Section '{section.title()}' in {file} still contains template text"
                )

            combined_authored_text += "\n" + body.lower()

    # -------------------------------------------------
    # Precision-based global judgment checks
    # -------------------------------------------------

    # Ownership must be explicit
    if not any(
        phrase in combined_authored_text
        for phrase in [
            " owns ",
            " owned by ",
            " accountable ",
            " responsible ",
            " ownership ",
        ]
    ):
        return False, "Decision ownership is not clearly demonstrated."

    # Containment or escalation reasoning must exist
    if not any(
        phrase in combined_authored_text
        for phrase in [
            "contain",
            "containment",
            "escalat",
            "stabiliz",
        ]
    ):
        return False, "Containment or escalation reasoning is missing."

    # Post-incident learning must be articulated
    if not any(
        phrase in combined_authored_text
        for phrase in [
            "learn",
            "learning",
            "improve",
            "prevent",
            "change",
        ]
    ):
        return False, "Post-incident learning is not articulated."

    return True, "Capstone project demonstrates structured incident leadership and ownership."
