# Identify bug introduction commit using git bisect

Objective:

Demonstrate expert-level ability to analyze Git commit history
and identify the exact commit where a regression was introduced
using systematic reasoning.

---
Requirements:

A Git repository must exist in the workspace.
The repository must contain both correct and faulty behavior
across different commits.

---
Task Requirements:

1. Analyze the Git commit history to determine where the regression began.
2. Identify the single commit that introduced the bug.
3. Create a file named bug_commit.txt.
4. The file must contain the full 40-character commit hash.
5. The file must contain no additional text or formatting.

---
Constraints:

Do NOT modify commit history.
Do NOT fix the bug.
Do NOT squash, amend, or rewrite commits.
Work fully offline using local repository state only.
