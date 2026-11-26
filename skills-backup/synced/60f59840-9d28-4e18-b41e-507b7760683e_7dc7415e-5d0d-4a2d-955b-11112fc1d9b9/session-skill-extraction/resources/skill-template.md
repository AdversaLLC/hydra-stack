---
name: descriptive-kebab-case-name
description: |
  [Key use first, then triggers. What this fixes or does, in one sentence.
  Use when: (1) exact error message or symptom, (2) tool/framework/file type,
  (3) situation. Keep description + when_to_use well under 1,536 characters.]
# Optional fields Claude Code acts on (delete the ones you don't need):
# when_to_use: Extra trigger phrases or example requests.
# paths: ["**/*.prisma", "prisma/**"]   # load only when matching files are in play
# disable-model-invocation: true        # only /name can run it (side-effect workflows)
# allowed-tools: [Read, Grep, Glob]     # tools pre-approved while the skill is active
# argument-hint: "[file-or-error]"
metadata:
  version: 1.0.0
  date: YYYY-MM-DD
  source: "[session/project where this was learned]"
---

# [Human-Readable Title]

## Problem

[What goes wrong and why it is non-obvious. Two or three sentences.]

## Trigger Conditions

- [Exact error message]
- [Observable symptom]
- [Environment: framework, tool, platform]

## Solution

1. [First action, with a command or code if needed]
2. [Next action]
3. [Alternatives or variants, if any]

## Verification

[The command or check that proves it worked, and the expected output.]

## Notes

- [Caveats, edge cases, when NOT to use this]
- [See also: related-skill-name]

## References

- [Official doc links consulted, if any]

<!--
Before saving (delete this block):
- Name is kebab-case and matches the folder name
- Description starts with the key use and includes exact error text/symptoms
- Solution was verified in the session; verification step is runnable
- No credentials, tokens or internal URLs
- Body is short: every line is a recurring token cost once loaded
-->
