# Evaluate dependency trade-offs under partial failure

Objective:

- Practice making trade-offs when a shared dependency is partially failing.
- Decide which functionality to preserve and which to degrade.
- Communicate expert-level judgment under ambiguity.

---
Requirements:

- A shared dependency is experiencing partial failure.
- Multiple services rely on this dependency with different criticality.
- The system state is preloaded to simulate a live production environment.
- The task must be completed fully offline.

---
Task Requirements:

- Review the dependency relationships, alerts, and metrics.
- Identify which services are most at risk.
- Decide which capabilities should be protected or degraded.
- Explain the trade-offs involved.
- Record your reasoning in **tradeoff-analysis.md**.

---
Constraints:

- Do NOT run commands or scripts.
- Do NOT propose permanent fixes.
- Do NOT assume perfect information.
- Focus on trade-offs and risk management, not resolution.
