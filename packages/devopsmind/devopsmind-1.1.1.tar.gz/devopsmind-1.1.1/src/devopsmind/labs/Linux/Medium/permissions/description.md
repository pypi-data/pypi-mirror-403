# Fix File Permissions

Objective:

- Practice managing Linux file permissions to enforce correct access control.
- Understand how ownership and permission bits affect who can read, write, and execute a file.
- Learn how restrictive permissions improve security by limiting access to sensitive scripts.

--
Requirements:

- The task must be completed using the local Linux filesystem.
- A file named script.sh must exist in the working directory.
- Permissions must be modified directly on the file rather than by recreating it.

---
Task Requirements:

- Create a file named script.sh in the working directory.
- Configure the file so that only the owner has read, write, and execute permissions.
- Remove all permissions for the group and others.
- Ensure the resulting permission mode is equivalent to 700.

---
Constraints:

- Do not grant any permissions to group or other users.
- Do not rely on default umask behavior alone.
- Do not use graphical file managers or permission editors.
- Validation is performed using static filesystem inspection only.

