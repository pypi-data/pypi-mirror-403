# Clean commit history using interactive rebase

Objective:

Demonstrate mastery of Git history rewriting by transforming
a messy feature branch into a single, clean, professional
commit suitable for production use.

---
Requirements:

A Git repository must exist in the workspace.
A feature branch named feature/refactor must already exist
and contain multiple commits.

---
Task Requirements:

1. Rewrite the history of the feature/refactor branch so that
   it contains exactly one commit.
2. The branch name must remain feature/refactor.
3. The final commit must have exactly one parent.
4. The final commit message must be exactly:
   Refactor core logic
5. Create a file named final_commit.txt containing the
   full 40-character commit hash of the final commit.

---
Constraints:

Do NOT merge branches.
Do NOT delete or rename the feature branch.
Do NOT modify the main branch.
Do NOT amend history after completing the rewrite.
Work fully offline using local Git state only.

