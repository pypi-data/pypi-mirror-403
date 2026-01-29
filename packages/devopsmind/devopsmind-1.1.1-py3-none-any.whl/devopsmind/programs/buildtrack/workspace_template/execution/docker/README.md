# Containerized Execution (Docker)

This directory represents how your application is packaged and executed
inside a container.

## Design writing

Document your design thinking in `DESIGN.md`.

Explain why containerization is used and what responsibility
the container owns.

## What you must create

Create a `Dockerfile` that satisfies all of the following:

- Specifies a base image appropriate for your application
- Defines a working directory inside the container
- Adds or copies application code or artifacts into the image
- Describes how the application is started at runtime
- Uses valid Dockerfile instructions throughout

The Dockerfile should clearly express intent and structure.

## Validation behavior

- The Dockerfile is required
- Instructions are parsed for valid Docker syntax
- Image quality, security, or optimization are not evaluated

