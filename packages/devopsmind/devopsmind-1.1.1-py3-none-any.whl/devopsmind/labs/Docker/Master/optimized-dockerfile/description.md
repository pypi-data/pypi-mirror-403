# Write an Optimized Dockerfile

Objective:

Write a production-quality Dockerfile that demonstrates
expert-level image optimization and best practices.

The goal is to minimize image size while preserving
clarity, correctness, and maintainability.

---
Requirements:

You must author a Dockerfile using only the provided guidance.
The Dockerfile must reflect realistic production container design.

---
Task Requirements:

Create a file named Dockerfile that satisfies all of the following:

- Uses python:3.10-slim as the base image
- Sets the working directory to /app
- Copies only app.py into the image
- Defines a single CMD that runs python app.py
- Does not use the latest tag
- Does not copy the entire build context

---
Constraints:

Do NOT install unnecessary packages
Do NOT copy files other than app.py
Do NOT build or run the container for validation
Work fully offline and locally

