# Design Argo CD Sync Behavior

Objective:

Demonstrate the ability to design and document Argo CD sync behavior
that explicitly defines how configuration drift and sync failures
are handled in a GitOps workflow.

---
Task Requirements:

You are provided with -

- `application.yaml` — an Argo CD Application template
- `sync-notes.md` — documentation for sync behavior decisions
- `logs/requirements.md` — required sync policy expectations
- `logs/sync-events.log` — example sync event evidence

You must - 

1. Edit `application.yaml` to define automated sync behavior, including:
   - Pruning behavior
   - Self-healing behavior
2. Edit `sync-notes.md` to document:
   - What happens when drift is detected
   - What happens when a sync fails and how it is surfaced

---
Constraints:

- Do NOT deploy to Kubernetes
- Do NOT add advanced hooks or custom health checks
- Do NOT invent platform behavior
- Focus on explicit, readable configuration and explanation
