# Design a Jenkins CI Pipeline with Failure Handling

Objective:

This lab focuses on **designing a Jenkins CI pipeline that handles failures
in a clear and maintainable way**.

In industry, CI pipelines are reviewed not only for success paths, but also for
how clearly they express failure conditions.


---
Requirements:

The pipeline must -

1. Include standard CI stages:
   - Checkout
   - Build
   - Test
2. Explicitly represent test failure handling
3. Be readable and maintainable


Provided Materials -

Failure Evidence
- `logs/sample-test.log`

Requirements
- `logs/requirements.md`

Templates
- `Jenkinsfile`
- `failure-notes.md`

---
Task Requirements:

1. Edit `Jenkinsfile` to design a CI pipeline that:
   - Includes all required stages
   - Clearly separates the Test stage
2. Edit `failure-notes.md` to:
   - Identify what failed
   - Explain how the pipeline surfaces this failure


Constraints:

- Do NOT execute Jenkins
- Do NOT invent tools or plugins
- Do NOT modify artifact files
- Focus on **design clarity**, not runtime behavior
