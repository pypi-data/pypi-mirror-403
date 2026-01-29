# Operational Judgment Doctrine — Severity Misclassification

This document defines the judgment standards applied in this challenge.
It does not describe correct actions or expected answers.

---

## Purpose of This Challenge

This challenge evaluates how human responders exercise judgment,
authority, and accountability when an automated system provides
advisory severity classifications during a production incident.

The focus is not on tools, models, or optimization.
The focus is on human decision-making under uncertainty.

---

## Decision Responsibility Model

In this environment:

- Automated systems may assess, classify, or recommend.
- Automated systems do not hold responsibility.
- Human responders retain full authority and accountability.

Accepting an automated judgment is itself a human decision.
Failing to override is also a decision.

Responsibility cannot be delegated to automation.

---

## What Constitutes a Judgment Failure

In this challenge, a judgment failure exists when:

- An automated severity classification is accepted without reassessment
  despite emerging operational or customer impact.
- Human authority exists but is not exercised at a critical moment.
- Responsibility for the outcome is diffused or left implicit.

Describing system behavior without identifying a human decision
is insufficient.

---

## Authority and Override Expectations

Human responders are expected to recognize:

- When automated severity assessments no longer match observed impact.
- When escalation authority should be exercised independent of AI output.
- When delaying intervention increases operational or business damage.

The absence of action is evaluated as deliberately as an action taken.

---

## Accountability Standard

A valid analysis assigns accountability to a decision-making role
(e.g., on-call engineer, incident commander, owning team).

Accountability does not require blaming individuals.
It requires naming where authority rested and how it was exercised.

Statements that attribute outcomes solely to “the system”,
“the process”, or “the AI” do not meet this standard.

---

## Post-Incident Control Expectations

After a judgment failure, acceptable responses focus on:

- Changes to authority boundaries
- Constraints on automated decision influence
- Conditions requiring mandatory human escalation or approval

Responses that focus only on improving models, alerts, or tooling
do not address the judgment failure evaluated in this challenge.

---

## Evaluation Boundary

This document defines how reasoning will be evaluated.
It does not reveal correct conclusions.

You are expected to apply these standards independently
to the incident presented in the challenge.
