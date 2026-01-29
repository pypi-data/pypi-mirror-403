# Configuration Packaging (Helm)

This directory represents how configuration is packaged
and reused across environments.

## Design writing

Document your design thinking in `DESIGN.md`.

Explain why templating or parameterization is needed.

## What you must create

Create Helm chart files that satisfy all of the following:

- Include a valid chart definition
- Define configurable values
- Use templates to express reusable structure
- Maintain valid YAML and Helm syntax

The focus is on configuration structure, not rendering output.

## Validation behavior

- Helm files are required
- Files are checked for syntax and basic structure
- Chart rendering and installation are not performed

