# Dockerfile that Copies a Local Script and Runs It

Objective:
Demonstrate understanding of how application code is copied
into a Docker image and executed when a container starts.

This lab focuses on Dockerfile structure and correctness,
not image building or runtime execution.

---
Requirements:

You must reason from the provided app.py file
and author a valid Dockerfile.

The Dockerfile must be syntactically correct
and reflect a realistic container workflow.

---
Task Requirements:

Create a Dockerfile that satisfies all of the following:

- Uses python:3.10-alpine as the base image
- Copies a local file named app.py into /app/app.py
- Sets the working directory to /app
- Defines a CMD that runs app.py using python3

---
Constraints:

Do NOT build or run the Docker image for validation
Do NOT use Docker Compose
Do NOT add unnecessary layers or optimizations
Validation is static and file-based only

