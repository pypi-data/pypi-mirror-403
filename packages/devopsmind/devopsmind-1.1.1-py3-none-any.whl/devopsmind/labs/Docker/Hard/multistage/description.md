# Build an Optimized Image with Multi-Stage Docker Build

Objective:
Create a Dockerfile that implements a multi-stage build
to produce an optimized runtime image.

The goal is to separate build-time dependency installation
from runtime execution while preserving application behavior.

---
Requirements:

You must author a Dockerfile using the provided app.py
and requirements.txt files.

The Dockerfile must use a multi-stage approach
and reflect realistic production container practices.

---
Task Requirements:

Create a Dockerfile that satisfies all of the following -

Stage 1 (builder) -
- Uses python:3.10-slim as the base image
- Copies requirements.txt and installs dependencies

Stage 2 (runtime) - 
- Uses python:3.10-slim as the base image
- Copies only installed dependencies and app.py
- Runs the application using python app.py

---
Constraints:

Do NOT include requirements.txt in the final image
Do NOT include build caches or tooling in the final image
Do NOT use Docker Compose
Work fully offline and locally

