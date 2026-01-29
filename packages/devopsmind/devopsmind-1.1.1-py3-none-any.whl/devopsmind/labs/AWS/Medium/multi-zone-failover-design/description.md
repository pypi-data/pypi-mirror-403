#  Assess a Multi-Zone Failover Strategy

Objective:

This lab verifies your ability to **assess a multi-Availability Zone
AWS web architecture under failure conditions**.

You are reviewing an existing architecture and a set of observed
failure events to determine whether **failover behaved as expected**.

This mirrors real-world incident reviews and resilience validation.

---
Provided Evidence:

You are given -

- A description of a highly available AWS web architecture  
  (`artifacts/architecture-requirements.md`)
- A log of observed infrastructure failures  
  (`artifacts/failure-events.log`)

These artifacts represent the **only information available**.

---
Task Requirements:

Edit the local file **`architecture-review.md`** and explain:

1. How the architecture is intended to handle Availability Zone failures
2. What happened during the observed failure event
3. Why user traffic continued to be served
4. Whether the observed behavior matches expected multi-AZ failover

Your response must reference **both the architecture description
and the failure events**.

---
Constraints:

- Do NOT design a new architecture
- Do NOT introduce additional AWS services
- Do NOT propose improvements
- Do NOT assume unmentioned behavior
- Work fully **offline and locally**
