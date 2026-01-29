# Alert Suppression and Operational Risk

Alert suppression reduces the number of alerts
presented to operators during incidents.

## Why Teams Introduce Suppression
- Alert storms during outages
- Cognitive overload for on-call engineers
- Difficulty identifying primary signals

## Known Failure Modes
- Important alerts suppressed incorrectly
- Partial failures masked by grouping
- Suppression persisting beyond safe conditions
- Operators unaware of what is hidden

## Stop-Line Concept
A stop-line is a predefined condition
where automation must disengage immediately,
without requiring interpretation or approval.

This document provides context only.
It does not define acceptable stop-lines.
