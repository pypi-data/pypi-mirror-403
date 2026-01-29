# Design a Read-Only Incident Analysis Agent

Objective:

- Design a safe, read-only AIOps agent that assists during incidents.
- Demonstrate engineering judgment around safety, boundaries, and human control.
- Ensure the agent provides insight without performing actions or changes.

---
Requirements:

Describe a read-only incident analysis agent by defining:
- The analytical purpose of the agent
- The categories of information it may observe
- Explicit boundaries it must not cross
- How human authority and accountability are preserved

Your design must make it impossible for the agent to act, decide, or accept risk on behalf of humans.
- You must edit and replace the contents of `agent_design.md`
  under the provided headings.

---
Task Requirements:

- Define the agent’s purpose during an incident.
- Specify what data the agent is allowed to read.
- Describe the agent’s decision flow for analyzing information.
- Explicitly state boundaries that the agent must not cross.
- Describe how human approval and control are preserved.

---
Constraints:

- The agent must be strictly read-only.
- No command execution or automated remediation.
- No configuration or state changes.
- No external APIs or cloud services.
- Offline reasoning only.
- Human accountability must remain intact.
