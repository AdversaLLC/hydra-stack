---
name: thefuck
description: After an agent-run shell command fails, use The Fuck to check for a safe correction when replaying the command cannot cause side effects; inspect any suggestion before retrying.
---

# The Fuck

Use this skill after a shell command you ran exits nonzero or clearly fails despite a zero exit status. It helps find a likely correction; it does not authorize a retry or make commands safe.

## Workflow

1. Preserve the exact command and its output. First decide whether the failure is a typo or command-construction issue that The Fuck might recognize.
2. Check that `thefuck` is installed. Do not install it as part of error recovery.
3. The Fuck normally reruns the selected command to capture its output. Invoke it only when repeating that exact command is safe and read-only. Do not invoke it for commands that change files or system state, require privilege, contact services, install packages, send data, deploy, or whose side effects are uncertain. In those cases, diagnose from the captured output instead.
4. In an agent shell tool, pass the failed command as `TF_HISTORY` and set `TF_SHELL` to the actual shell (for example, `TF_SHELL=bash TF_HISTORY='failed command' thefuck`); allocate a PTY if its interactive selector requires one. For an ordinary interactive Bash shell, use the configured `fuck` function.
5. Read the proposed command without auto-accepting it. Never use `--yes`, `--yeah`, `--hard`, or an equivalent option. Cancel the selector after recording the candidate, then validate the candidate against the original intent and current evidence.
6. Run a corrected command only when it is plainly safe, within the user's existing authorization, and you have checked every added flag, path, privilege escalation, and chained command. Otherwise explain the proposal or ask before acting.
7. Retry at most once through this recovery path. If it fails again, inspect the new error and switch to ordinary diagnosis rather than repeatedly invoking The Fuck.

## Do not route here

- Failures whose cause is already clear from the output, such as unavailable network, failed package signatures, missing permissions, or a stale service.
- Commands with non-read-only or uncertain effects, even if they look like simple typos.
- Errors from non-shell tools; handle those using their own diagnostics.

The host may not expose the skill until its skill catalog refreshes. In that case, invoke `$thefuck` explicitly when recovering from a failed shell command.
