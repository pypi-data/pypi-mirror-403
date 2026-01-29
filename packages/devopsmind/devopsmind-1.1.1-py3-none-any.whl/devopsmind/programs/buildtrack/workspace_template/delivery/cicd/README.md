# Continuous Integration & Delivery

This directory represents how changes are validated
and automated before release.

## Design writing

Document your design thinking in `DESIGN.md`.

Explain how automation builds confidence in changes
and what responsibilities the CI/CD layer owns.

## What you must create

Create one or more CI/CD configuration files that satisfy all of the following:

- Use a valid declarative configuration format
- Represent an automated pipeline or workflow
- Define stages or jobs involved in change validation
- Express the order or flow of automation
- Reflect process and intent, not tool-specific mastery

You may choose any CI/CD system.

Common examples include (but are not limited to):
- `Jenkinsfile`
- `.github/workflows/*.yml`
- `.gitlab-ci.yml`
- `.circleci/config.yml`

## Validation behavior

- At least one CI/CD configuration file is required
- Files are parsed for syntax only
- Pipelines are not executed or simulated
