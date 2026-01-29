# Squash-merge a feature branch cleanly into main

Objective:

Demonstrate the ability to integrate a feature branch into main
using a squash-merge strategy that preserves a clean, linear
Git history suitable for production repositories.

---
Requirements:

A Git repository must exist with:
- a main branch
- a feature branch named feature/login

---
Task Requirements:

1. On the main branch, integrate feature/login using a squash strategy.
2. The integration must result in exactly ONE new commit on main.
3. The commit message on main must contain the substring:
   Add auth feature
4. After integration, login.txt must exist on main and contain exactly:
   login implemented

---
Constraints:

Do NOT create merge commits.
Do NOT leave multiple feature commits on main.
Do NOT rewrite main history after the squash.
Work fully offline using local Git state only.

