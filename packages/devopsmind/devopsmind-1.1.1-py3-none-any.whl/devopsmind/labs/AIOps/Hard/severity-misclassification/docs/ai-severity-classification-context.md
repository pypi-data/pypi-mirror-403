# AI Incident Severity Classification Context

This lab evaluates human judgment and accountability when automated systems
provide advisory assessments during production incidents.

The AI system assigns incident severity levels using historical patterns,
correlation signals, and confidence scoring. These assessments are advisory
and do not execute remediation or enforce response actions.

Severity classification influences:
- Escalation urgency
- On-call engagement timing
- Incident prioritization

In operational use, human responders retain full authority to:
- Accept or override severity classifications
- Escalate incidents independent of AI output
- Reassess impact as new operational signals emerge

The learning focus of this lab is identifying:
- When an automated severity judgment is incorrect or insufficient
- The moment human authority should override automation
- How a human decision (or lack of one) directly affects operational
  and business outcomes

During the incident represented in this lab:
- A multi-service production issue occurred
- An initial severity classification influenced early response behavior
- Customer-facing impact increased before escalation occurred

This context does not prescribe correct actions.
Learners are expected to reason about judgment, authority, and accountability
under uncertainty.
