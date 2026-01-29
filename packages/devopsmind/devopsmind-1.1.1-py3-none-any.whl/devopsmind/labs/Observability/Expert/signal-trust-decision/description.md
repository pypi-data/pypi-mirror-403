# Decide which observability signals to trust during an incident

Objective:

- Practice evaluating conflicting observability signals.
- Decide which data sources are reliable enough to guide decisions.
- Demonstrate expert judgment when observability itself is uncertain.

---
Requirements:

- Metrics, logs, and alerts provide conflicting information.
- Some observability components may be degraded.
- The system state is preloaded to simulate a live incident.
- The task must be completed fully offline.

---
Task Requirements:

- Review all provided observability signals.
- Identify conflicts or inconsistencies between signals.
- Decide which signals are trustworthy and which are suspect.
- Explain how your trust decisions affect incident handling.
- Record your analysis in **signal-trust-assessment.md**.

---
Constraints:

- Do NOT run commands or scripts.
- Do NOT assume all observability data is correct.
- Do NOT discard signals without justification.
- Focus on trust assessment, not root cause resolution.
