# Design a Secure Multi-Stage Dockerfile

Objective:

Design a secure multi-stage Dockerfile that demonstrates
expert-level container security practices.

The goal is to minimize attack surface and enforce
least-privilege execution in the final image.

---
Requirements:
You must author a Dockerfile using a multi-stage build.
The final image must run the application as a non-root user
and include only runtime-required artifacts.

---
Task Requirements:

Create a Dockerfile that satisfies all of the following:

Stage 1 (builder) -
- Uses python:3.10-slim as the base image
- Installs dependencies from requirements.txt

Stage 2 (runtime) -
- Uses python:3.10-slim as the base image
- Copies only installed dependencies and app.py
- Creates and switches to a non-root user
- Runs the application using python app.py

---
Constraints:

Do NOT copy requirements.txt into the final image
Do NOT run the container as root
Do NOT use Docker Compose
Work fully offline and locally

