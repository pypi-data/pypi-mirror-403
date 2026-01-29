# AIOps Agent Failure Analysis

# Failure Description
Describe what the agent did incorrectly.

Include:
- What the agent suggested
- Why the suggestion was wrong
- When the error was detected

---

# Impact
Explain the operational impact.

Consider:
- Incident duration
- Service degradation
- Engineering response delay
- User or business impact

---

# Root Cause
Analyze why the failure occurred.

Focus on:
- AI uncertainty or hallucination
- Incomplete or misleading inputs
- Over-trust in agent output
- Missing safeguards

Avoid blaming individuals.

---

# Containment
Describe how the situation should be controlled once detected.

Examples:
- Disable agent output
- Escalate to human-only analysis
- Preserve audit logs
- Communicate uncertainty clearly

---

# Prevention
Propose system-level changes to reduce future risk.

Examples:
- Confidence thresholds
- Stronger human review gates
- Output disclaimers
- Narrower agent scope

Do NOT suggest autonomous remediation.
