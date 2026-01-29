# Operational Judgment Doctrine — AIOps Agent Failure

This document defines the judgment standards applied in this challenge.
It does not describe expected answers or corrective actions.

---

## Purpose of This lab

This lab evaluates how engineers assess, contain, and prevent risk
when an AIOps agent produces an incorrect or unsafe recommendation.

The focus is on judgment, authority, and accountability — not tooling
or model optimization.

---

## Responsibility and Authority

In this environment:

- AIOps agents may recommend actions or interpretations
- AIOps agents do not hold responsibility
- Human engineers retain full authority and accountability

Accepting an agent recommendation is a human decision.
Failing to question or contain an agent is also a decision.

Responsibility cannot be delegated to automation.

---

## Judgment Failure Standard

A judgment failure exists when:

- Agent output is accepted without sufficient skepticism
- Known uncertainty is not communicated or escalated
- Containment is delayed after unsafe behavior is detected

Describing agent behavior without identifying a human decision
does not meet this standard.

---

## Containment and Control Expectations

Once an agent failure is detected, acceptable responses focus on:

- Limiting or disabling unsafe agent influence
- Reverting to human-only analysis
- Preserving evidence and auditability
- Clearly communicating uncertainty and risk

Autonomous remediation is explicitly out of scope.

---

## Prevention Scope

Preventive actions must address:

- Authority boundaries
- Review and approval gates
- Confidence thresholds or scope limitations

Preventive reasoning focused solely on retraining or tuning
does not address the judgment failure evaluated here.

---

## Evaluation Boundary

This document defines how reasoning will be evaluated.
It does not prescribe correct conclusions.

You are expected to apply these standards independently
to the incident presented in the challenge.
