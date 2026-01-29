# Perform Root Cause Analysis for Argo CD Sync Failure

Objective:

Perform a structured **Root Cause Analysis (RCA)** for an Argo CD Application
that failed to synchronize, using only declarative GitOps evidence.

The goal is to demonstrate disciplined, evidence-based reasoning rather than
trial-and-error debugging.

---
Task Requirements:

You are provided with **read-only evidence** -

- `manifests/application.yaml`
- `manifests/sync-events.log`
- `manifests/failure-timeline.md`

You must complete -

- `rca.md`

Your RCA must clearly include:
1. Observed failure
2. Root cause
3. Contributing factors
4. Corrective action

Every conclusion must be supported by the provided evidence.

---
Constraints:

- Do NOT deploy or sync using Argo CD
- Do NOT modify evidence files
- Do NOT invent platform behavior
- Analysis must remain declarative and offline
