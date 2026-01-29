# Determine Cause of a Regional Service Collapse

Objective:
Verify the learner’s ability to perform a deep architectural Root Cause Analysis (RCA)
for a production AWS outage that resulted in a regional service collapse.

Although the initial failure occurred within a single Availability Zone,
the entire service in the region degraded due to architectural and capacity limitations.

---
Requirements:

The learner must reason strictly from the provided evidence artifacts.
No assumptions about live AWS behavior or hidden infrastructure are allowed.

---
Task Requirements:

Edit the local file rca.md and document:
1. What users across the region experienced
2. The primary architectural cause of the regional service collapse
3. Contributing architectural or capacity-related factors
4. Why the region could not absorb or stabilize after the failure

The analysis must explain failure propagation, not just the initial failure.

---
Constraints:

Do NOT propose fixes or redesigns.
Do NOT reference tooling, IaC, deployments, or AWS configuration commands.
Do NOT invent AWS behavior.
Base conclusions strictly on provided evidence.
Work fully offline and locally.

---
Rules:

Only rca.md may be modified by the learner.
All validation is static and performed by validator.py.
Execution or experimentation is not required for validation.
