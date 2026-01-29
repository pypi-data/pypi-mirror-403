# Resolve Task Dependencies

Objective:

Demonstrate expert-level algorithmic reasoning by resolving task
dependencies and producing a valid execution order.

This lab evaluates understanding of dependency graphs and
ordering constraints commonly found in build systems and automation
workflows.

---
Requirements:

- The solution must be written in Python.
- Only the Python standard library may be used.
- The program must compute the execution order dynamically.

---
Task Requirements:

You are given a dependency definition describing relationships
between tasks.

Each relationship indicates that one task depends on another
and must be executed after it.

Create a Python file named resolve_deps.py that:

- Computes a valid execution order for all tasks
- Ensures each dependency is executed before the task that depends on it
- Prints each task name on a separate line

The output order must satisfy all dependency constraints.

---
Constraints:

- Do NOT hardcode the execution order
- Do NOT assume a specific task ordering beyond dependencies
- Cycles do NOT exist in the dependency graph
- Validation is static and execution-based only

