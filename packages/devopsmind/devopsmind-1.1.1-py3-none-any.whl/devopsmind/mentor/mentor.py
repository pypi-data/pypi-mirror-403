# src/devopsmind/mentor/mentor.py

from rich.panel import Panel
from rich.text import Text
from rich.console import Console, Group

from devopsmind.mentor.engine import get_mentor_advice

console = Console()


def _trend_for(label: str) -> str:
    if "Confident" in label:
        return "rising"
    if "Familiar" in label:
        return "steady"
    return "building"


def _tone_prefix(label: str) -> str:
    if "Confident" in label:
        return "You’re operating from a position of strength here."
    if "Familiar" in label:
        return "Your understanding here is stable and reliable."
    return "You’re laying the foundations here — keep going."


def _why_for_recommendations(recommendations):
    stacks = [c.get("stack") for c in recommendations if c.get("stack")]
    difficulties = [c.get("difficulty") for c in recommendations if c.get("difficulty")]

    if not stacks:
        return "These labs help you maintain steady momentum in this tier."

    unique_stacks = list(dict.fromkeys(stacks))
    unique_difficulties = set(difficulties)

    if len(unique_stacks) == 1:
        return (
            f"These labs deepen your confidence in {unique_stacks[0].title()}, "
            "helping you consolidate understanding before moving on."
        )

    if len(unique_difficulties) == 1:
        diff = next(iter(unique_difficulties))
        stacks_text = ", ".join(s.title() for s in unique_stacks)
        return (
            f"These labs focus on {stacks_text} while keeping difficulty "
            f"at a steady {diff} to support consistent progress."
        )

    stacks_text = ", ".join(s.title() for s in unique_stacks)
    return f"These labs reinforce multiple stacks ({stacks_text}) at a balanced pace."


def _render_confidence_block(body, title, confidence):
    body.append(Text(f"\nConfidence snapshot ({title}):\n", style="bold"))
    body.append(
        Text(
            "A qualitative view of how comfortable you are working in this tier, "
            "based only on labs completed within it.",
            style="dim",
        )
    )

    for stack, data in confidence.items():
        label = data["label"]
        trend = _trend_for(label)
        tone = _tone_prefix(label)

        body.append(Text(f"• {stack.title():12} → {label} · {trend}"))
        body.append(Text(f"  ↳ {tone}", style="dim"))


def run_mentor():
    advice = get_mentor_advice()
    body = []

    body.append(
        Text(
            "A mentor’s role is to guide direction, not give answers.\n",
            style="dim",
        )
    )

    # -------------------------------------------------
    # ✅ RECOMMENDATIONS (PER TIER)
    # -------------------------------------------------
    recommendations_by_tier = advice.get("recommendations_by_tier", {})

    if recommendations_by_tier:
        for tier_name, recos in recommendations_by_tier.items():
            body.append(Text(f"\n🧭 Recommended next labs ({tier_name})\n", style="bold"))

            for c in recos:
                stack = c.get("stack", "unknown").title()
                difficulty = c.get("difficulty", "—")

                body.append(
                    Text(
                        f"▶ {c['id']} — {c['title']} [{stack} · {difficulty}]",
                        style="cyan",
                    )
                )

                if c.get("reason"):
                    body.append(Text(f"  ↳ {c['reason']}", style="dim"))

            body.append(Text("\nWhy these labs:\n", style="bold"))
            body.append(Text(_why_for_recommendations(recos)))
    else:
        body.append(Text("\n🧭 Recommendations\n", style="bold"))
        body.append(
            Text(
                "No lab recommendations are available yet.\n"
                "Complete at least one lab or ensure your lab access is unlocked, "
                "and the mentor will guide you forward.",
                style="dim",
            )
        )

    # -------------------------------------------------
    # ✅ CONFIDENCE (PER TIER)
    # -------------------------------------------------
    confidence_by_tier = advice.get("confidence_by_tier", {})

    for tier_name, confidence in confidence_by_tier.items():
        _render_confidence_block(body, tier_name, confidence)

    # -------------------------------------------------
    # Learning style
    # -------------------------------------------------
    style = advice.get("learning_style", {})
    body.append(Text("\nLearning style insight:\n", style="bold"))
    body.append(Text(style.get("label", "—")))
    body.append(Text(style.get("explanation", "")))

    # -------------------------------------------------
    # Weekly cadence
    # -------------------------------------------------
    body.append(Text("\nWeekly cadence suggestion:\n", style="bold"))
    body.append(Text(advice.get("cadence", "—")))

    # -------------------------------------------------
    # Stagnation notice
    # -------------------------------------------------
    if advice.get("stagnation"):
        body.append(Text("\nMentor notice:\n", style="bold yellow"))
        body.append(Text(advice["stagnation"]))

    console.print(
        Panel(
            Group(*body),
            title="🧭 DevOpsMind Mentor",
            border_style="cyan",
        )
    )
