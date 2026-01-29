# Analyze regression after partial mitigation

Objective:

- Identify regression after an incident mitigation.
- Distinguish temporary stabilization from true resolution.
- Perform disciplined RCA when symptoms reappear.

---
Requirements:

- Metrics and alerts before and after mitigation are provided.
- The system state represents a production service under recovery.
- The task must be completed fully offline.

---
Task Requirements:

- Review metrics and alerts across the full time window.
- Identify when mitigation occurred and what changed.
- Determine why the issue reappeared after initial improvement.
- Produce a structured root cause analysis.
- Record your analysis in **rca.md**.

---
Constraints:

- Do NOT run commands or scripts.
- Do NOT modify evidence files.
- Do NOT assume mitigation equals resolution.
- Do NOT speculate beyond available evidence.
- Focus on evidence across time.
