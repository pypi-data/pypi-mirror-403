# src/devopsmind/programs/command_policy.py

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandPolicy:
    allowed: list[str]
    blocked: list[str]


# ------------------------------------------------------------
# BuildTrack Policy (PROGRAM CONTENT)
# ------------------------------------------------------------

def buildtrack_policy_for_stage(stage: int) -> CommandPolicy:
    """
    Command unlock policy for BuildTrack program,
    based on progression stage.
    """
    if stage <= 1:
        return CommandPolicy(
            allowed=["ls", "cat", "mkdir", "tree"],
            blocked=["docker", "kubectl", "terraform"],
        )

    if stage <= 3:
        return CommandPolicy(
            allowed=[
                "ls",
                "cat",
                "mkdir",
                "tree",
                "git",
                "docker",
            ],
            blocked=["kubectl", "terraform"],
        )

    return CommandPolicy(
        allowed=["*"],
        blocked=[],
    )


# ------------------------------------------------------------
# InfraHack Policy (PROGRAM CONTENT – FUTURE)
# ------------------------------------------------------------

def infrahack_policy() -> CommandPolicy:
    """
    InfraHack is challenge-based:
    - No gradual unlock
    - All tools available
    """
    return CommandPolicy(
        allowed=["*"],
        blocked=[],
    )


# ------------------------------------------------------------
# Policy Resolver (ENGINE LEVEL)
# ------------------------------------------------------------

def get_command_policy(program: str, stage: int | None = None) -> CommandPolicy:
    """
    Resolve command policy for a given program.
    """
    match program:
        case "buildtrack":
            return buildtrack_policy_for_stage(stage or 0)

        case "infrahack":
            return infrahack_policy()

        case _:
            # Safe default: very restrictive
            return CommandPolicy(
                allowed=["ls", "cat"],
                blocked=["*"],
            )
