# Linux Execution Environment

This directory represents the operating system layer
your system depends on.

It exists to make explicit what responsibilities are
owned by the OS and what assumptions higher layers rely on.

## Design writing

Document your design thinking in `DESIGN.md`.

Explain:
- why Linux is used as the execution environment
- what responsibilities are handled at the OS level
- what assumptions the system makes about the host

This file should reflect your own understanding, not the template questions.

## What you must create

Create one or more shell scripts that express **OS-level intent**.

The scripts should:
- Be valid POSIX-compatible shell scripts
- Represent system-level responsibilities such as:
  - environment preparation
  - filesystem layout assumptions
  - user or permission boundaries
  - runtime prerequisites
- Use clear structure, comments, and readable naming
- Communicate responsibility even if not executed

The goal is **not** to fully automate setup,
but to show what the operating system layer owns.

## What this layer does *not* require

- Scripts do not need to be production-ready
- Scripts are not expected to run successfully
- Error handling and optimization are optional
- Real system modification is not evaluated

## Validation behavior

- At least one `.sh` file is required
- Scripts are checked for basic shell syntax
- Script behavior is not executed or judged

Validation confirms intent, not correctness.
