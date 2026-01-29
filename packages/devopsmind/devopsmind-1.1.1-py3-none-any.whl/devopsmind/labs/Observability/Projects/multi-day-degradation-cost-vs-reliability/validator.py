import os

REQUIRED = {
    "degradation-assessment.md": [
        "current state",
        "user impact",
        "stability trend",
        "acceptable degradation",
        "ownership",
    ],
    "cost-reliability-decision.md": [
        "options considered",
        "decision",
        "rationale",
        "risks accepted",
        "ownership",
    ],
    "executive-response.md": [
        "executive concerns",
        "response strategy",
        "commitments",
        "risks communicated",
        "ownership",
    ],
    "long-term-plan.md": [
        "lessons learned",
        "structural changes",
        "cost control strategy",
        "irreversible decisions",
        "ownership",
    ],
}

# Only instructional sentence starters — not general English words
PLACEHOLDER_STARTS = [
    "describe ",
    "state ",
    "identify ",
    "summarize ",
    "explain ",
    "define ",
]

def extract_section(content: str, section_title: str) -> str | None:
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
    text = text.strip().lower()

    # Catch untouched template blocks like "(Describe ...)"
    if text.startswith("(") and text.endswith(")"):
        return True

    # Catch instructional sentences only if they START the section
    return any(text.startswith(p) for p in PLACEHOLDER_STARTS)


def validate():
    combined_authored_text = ""

    for file, sections in REQUIRED.items():
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
                    f"Section '{section.title()}' in {file} still contains template text",
                )

            combined_authored_text += "\n" + body.lower()

    # -------------------------------------------------
    # Precision-based global judgments
    # -------------------------------------------------

    # Ownership must be explicit and singular
    if not any(
        w in combined_authored_text
        for w in [
            " owns ",
            " owned by ",
            " accountable ",
            " responsible ",
            " ownership ",
        ]
    ):
        return False, "Decision ownership is not clearly stated."

    # Trade-offs must be acknowledged explicitly
    if not any(
        w in combined_authored_text
        for w in [
            "trade-off",
            "tradeoff",
            "balance",
            "risk",
            "accept",
            "sacrifice",
            "cost increase",
        ]
    ):
        return False, "Trade-offs are not explicitly acknowledged."

    # Cost vs reliability reasoning must exist
    if not ("cost" in combined_authored_text and "reliab" in combined_authored_text):
        return False, "Cost vs reliability reasoning is missing."

    return True, "Capstone demonstrates senior-level cost vs reliability judgment."
