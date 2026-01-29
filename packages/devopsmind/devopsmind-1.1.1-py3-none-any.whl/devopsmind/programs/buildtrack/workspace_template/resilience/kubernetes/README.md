# Workload Resilience (Kubernetes)

This directory represents how your system behaves
when components fail or restart.

## Design writing

Document your design thinking in `DESIGN.md`.

Explain how resilience is achieved at runtime.

## What you must create

Create Kubernetes YAML manifests that satisfy all of the following:

- Are valid YAML documents
- Define one or more Kubernetes resources
- Include required structural fields such as:
  - apiVersion
  - kind
  - metadata
  - spec
- Describe desired state rather than imperative actions

The manifests should reflect intent, not operational completeness.

## Validation behavior

- YAML files are required
- Files are parsed for syntax and basic structure
- No cluster execution or scheduling validation is performed
