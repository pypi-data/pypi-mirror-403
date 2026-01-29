# Investigate a Permission Sprawl Incident

Objective:
Verify the learner’s ability to perform an Expert-level
cloud security incident analysis focused on blast radius
and trust boundary reasoning.

The incident escalated not due to a single vulnerability,
but because identity and resource boundaries were weakly defined.

---
Requirements:

Learners must reason strictly from the provided evidence artifacts.
No assumptions about live AWS behavior or tooling are permitted.

---
Task Requirements:

Edit the local file security-analysis.md and document:
1. The effective security boundaries present in the architecture
2. How the incident propagated beyond the initially compromised instance
3. Which trust boundaries failed to limit blast radius
4. Why the blast radius was larger than expected

The analysis must be evidence-based and focused on
identity, trust, and access boundaries.

---
Constraints:

Do NOT propose fixes or redesigns
Do NOT reference IAM policy syntax, tooling, or consoles
Do NOT invent AWS behavior
Work fully offline and locally

---
Rules:

Only security-analysis.md may be modified by the learner.
All validation is static and performed by validator.py.
Execution is not required for validation.

