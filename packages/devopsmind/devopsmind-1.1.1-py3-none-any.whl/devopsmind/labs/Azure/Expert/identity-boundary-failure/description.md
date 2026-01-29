# Examine an Identity Boundary Failure

Objective:
This lab verifies your ability to perform an Expert-level
security architecture analysis focused on identity boundaries
and blast radius in Azure.

The incident did not escalate because of a single exploit.
It escalated because identity scope and trust boundaries
were too broad.

Your task is to explain why the architecture allowed lateral spread.

---
Requirements:

You must reason strictly from the provided architecture context,
security boundary definitions, and incident evidence.

No assumptions about unobserved Azure behavior are allowed.

---
Task Requirements:

Edit the local file security-analysis.md and document:

1. The effective identity, network, and resource boundaries
2. How access expanded beyond the initially compromised VM
3. Which boundaries failed to limit blast radius
4. Why the blast radius was larger than expected

Your analysis must be strictly evidence-based.

---
Constraints:

Do NOT propose fixes or redesigns
Do NOT reference Azure Portal steps or tooling
Do NOT invent Azure behavior
Focus on identity scope, trust, and blast radius
Work fully offline and locally

