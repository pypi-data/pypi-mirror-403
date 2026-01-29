# Declarative Delivery (GitOps)

This directory represents how deployments are driven
by declared state stored in version control.

## Design writing

Document your design thinking in `DESIGN.md`.

Explain why declarative delivery is used,
what responsibilities this layer owns,
and how safety or rollback is achieved.

## What you must create

Create one or more declarative deployment configuration files
that satisfy all of the following:

- Use a valid declarative configuration format (YAML)
- Describe desired runtime state rather than execution steps
- Represent configuration owned by version control
- Support change through versioned updates
- Avoid imperative commands or scripts

The files should express intent and structure,
not operational completeness.

Common examples include (but are not limited to):
- Kubernetes manifests
- environment-specific configuration YAML
- GitOps-managed desired state definitions

## Validation behavior

- At least one declarative manifest file is required
- Files are parsed for syntax only
- No reconciliation, sync, or runtime validation is performed

