# Feature branch and rebase

Objective:

Practice clean Git history management by rebasing a feature branch
onto the latest main branch without introducing merge commits.

This lab evaluates understanding of rebasing semantics,
not command memorization.

---
Requirements:

A Git repository with an existing main branch must be present.
The repository must allow branch creation and rebasing.

---
Task Requirements:

1. Create a branch named feature/login.
2. On feature/login, create a file named login.txt containing exactly:
   login implemented
3. Commit the change on feature/login.
4. Rebase feature/login onto the latest main branch.
5. Do NOT create a merge commit.
6. Leave the feature/login branch present locally.

---
Constraints:

Do NOT create merge commits.
Do NOT modify commit history after rebasing.
Do NOT use interactive rebase options.
Work fully offline using local Git state only.

