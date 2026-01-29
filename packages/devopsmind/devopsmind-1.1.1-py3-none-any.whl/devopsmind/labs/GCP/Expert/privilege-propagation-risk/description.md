# Analyze Privilege Propagation Risk

Objective:

Perform an expert-level security architecture analysis
focused on privilege propagation and blast radius
in a GCP environment.

The goal is to explain why a localized compromise
expanded beyond its initial scope.

---
Requirements:

Your analysis must be based strictly on the provided
architecture description, security boundaries,
and incident evidence.

All conclusions must be evidence-based.

---
Task Requirements:

Edit the local file security-analysis.md and document:

1. The effective identity, network, and resource boundaries
2. How access expanded beyond the initially compromised instance
3. Which trust boundaries failed to limit blast radius
4. Why the blast radius was larger than expected

---
Constraints:

Do NOT propose fixes or redesigns
Do NOT reference IAM syntax or tooling
Do NOT assume console access
Do NOT invent GCP behavior
Work fully offline and locally

