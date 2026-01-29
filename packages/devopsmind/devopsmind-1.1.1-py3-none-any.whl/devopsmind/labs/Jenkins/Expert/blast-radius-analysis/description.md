# Analyze Jenkins Shared Pipeline Impact

Objective:

Analyze the blast radius of shared Jenkins pipeline logic and determine
how failures in a common CI component can impact multiple independent
pipelines across the system.

This lab evaluates expert-level reasoning about CI architecture,
hidden coupling, and failure propagation rather than pipeline execution
or tooling.

---
Requirements:

- The analysis must be written as a structured impact assessment
- Only the provided CI manifests and documentation may be used
- The solution must be performed fully offline
- No Jenkins execution or configuration is required
- Reasoning must focus on system-wide impact, not individual failures

---
Task Requirements:

- Review the provided Jenkins pipeline manifests and shared components
- Identify the shared CI component that introduces coupling
- List all pipelines affected by this shared component
- Explain how a failure in the shared logic propagates across pipelines
- Propose one concrete recommendation to reduce blast radius
- Write the analysis in impact-analysis.md using clear technical reasoning

---
Constraints:

- Do NOT execute Jenkins or pipelines
- Do NOT modify provided manifests or files
- Do NOT invent dependencies not shown in the evidence
- Do NOT propose tooling or automation solutions
- Base all conclusions strictly on the provided CI artifacts

