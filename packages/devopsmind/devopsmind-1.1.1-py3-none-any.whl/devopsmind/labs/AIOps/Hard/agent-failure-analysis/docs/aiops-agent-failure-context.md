# AIOps Agent Failure Context

This challenge involves an AIOps agent used to assist engineers during
production incidents.

The agent provides recommendations based on telemetry, historical data,
and correlation signals. These recommendations may influence human
decision-making but do not execute changes or remediation actions.

In operational use:
- The agent operates in advisory mode only
- Human engineers retain full authority over incident response
- Agent output may be incomplete, uncertain, or incorrect

During the incident represented in this challenge:
- The agent produced a recommendation that influenced the response
- The recommendation was later determined to be incorrect or unsafe
- Operational impact occurred before the failure was fully understood

This document provides environmental context only.
It does not describe correct or incorrect actions.
