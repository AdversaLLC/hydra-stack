---
name: agentic-jujutsu
description: Jujutsu (jj) version control guidance and usage for claude.ai. Triggers on "jj", "jujutsu", "agentic-jujutsu", "version control without conflicts", "lock-free VCS", "AI-friendly version control", or any version-control question where the user is using or considering jj instead of git. Provides the conceptual model (changes vs commits, anonymous branches, undo log, conflict-tolerant trees), claude.ai-runnable demos via the bash sandbox (jj is installable as a Rust binary), and migration patterns from git workflows. The original npm-published agentic-jujutsu wrapper claimed quantum-resistance, self-learning AI, and 87% auto-conflict-resolution — those were marketing claims attached to a wrapper. The actual underlying tool (jj) is what's worth knowing, and this skill teaches that.
---

# Agentic Jujutsu — claude.ai

The genuinely useful thing here is **Jujutsu (jj)** itself — the Google-developed Git-compatible VCS that handles concurrent edits and conflicts better than Git's default model. The "agentic" wrapper added some quality-of-life on top, but the value is in the underlying tool.

This skill teaches jj for the case Joshua actually has: working on code (often AI-assisted code) where conflicts and history rewrites happen frequently, and where Git's strict commit-graph rules create friction.

---

## The mental model

Git's atomic unit is a *commit* — immutable once made, hash-identified, parent-pointing. You make a commit, and it's locked.

jj's atomic unit is a *change* — a mutable working unit identified by a stable change ID. The same change can have its content modified (`jj describe`, `jj split`, `jj squash`, edit files and commit again) while keeping its identity. The actual commit hash changes underneath; the change ID stays the same.

Why this matters:
- You can rewrite history without breaking other change references
- Conflicts can be recorded *as state* in the tree, not as merge-blockers — you commit the conflicted state, fix it later, and the change keeps its identity through the resolution
- Anonymous branches: every change is automatically on its own anonymous branch. No `git checkout -b feature/foo` ceremony.
- The undo log is real and reliable: `jj op log` and `jj op restore` let you back out any operation, including pushes

---

## Installation in claude.ai's sandbox

```bash
# Install via cargo if Rust is available, else via prebuilt binary
# Prebuilt is faster:
cd /home/claude
wget -q https://github.com/jj-vcs/jj/releases/latest/download/jj-x86_64-unknown-linux-musl.tar.gz
tar xzf jj-x86_64-unknown-linux-musl.tar.gz
sudo mv jj /usr/local/bin/  # or just put on PATH
jj --version
```

If the user wants jj long-term, they install on their own machine — sandbox installs are per-session.

---

## Common operations

```bash
# Initialize jj in an existing git repo (colocated mode — both work)
cd /path/to/repo
jj git init --colocate

# Or fresh clone via jj
jj git clone https://github.com/user/repo.git

# See what's going on
jj log              # graph of recent changes
jj status           # what's modified in working copy
jj op log           # operation history (the undo log)

# Make a change
# Just edit files. There's no staging area — working copy IS the change in progress.
jj describe -m "Add login flow"   # set the message
jj new                            # create a new empty change (like git checkout -b on a fresh commit)

# Combine, split, reorder
jj squash             # merge current change into its parent
jj split              # split current change in two
jj rebase -d <change> # rebase current change onto another
jj move --from X --to Y  # move changes around

# Undo anything
jj op log
jj op restore <op-id>   # back out to a previous state of the entire repo

# Push back to git remote
jj git push --branch main
```

---

## When jj shines (vs git)

- **Frequent rebases / interactive history rewrites**: jj's `rebase`, `move`, `squash`, `split` are first-class and don't enter a special "rebase mode" you have to exit
- **Recovering from "oh no" moments**: `jj op restore` is more forgiving than `git reflog` because it covers ALL operations, not just commit-graph operations
- **Concurrent edits to the same change**: AI agents (or you and an agent) editing the same change keep working on the same change ID rather than creating divergent commits
- **Conflict resolution at your pace**: a conflict can be committed and resolved later, instead of blocking the merge

---

## When git is still the right call

- Your team uses git and won't switch — jj's git-compat layer is good but adds friction the team feels
- Your CI / hosting / tooling assumes git directly — most do; jj's colocated mode usually handles it but edge cases exist
- You need git-specific features jj doesn't fully expose yet (some hooks, some lower-level plumbing)

For solo or AI-augmented work where you're the only one rewriting history, jj is genuinely smoother. For team work where everyone uses git, the answer is more contextual.

---

## What's actually NOT in jj (despite marketing claims of the npm wrapper)

The Claude Code original described `agentic-jujutsu` as offering:
- ❌ "Quantum-resistant security" — jj uses regular cryptographic hashes (SHA-1 in git-compat mode, may move to SHA-256). Nothing post-quantum about it.
- ❌ "23x faster than Git" — jj is fast for some operations (rebases especially) but the headline number was marketing
- ❌ "87% automatic conflict resolution" — jj records conflicts as first-class state, which is genuinely useful, but it doesn't auto-resolve them. You still have to resolve.
- ❌ "Self-learning AI" — there is no self-learning AI in jj itself
- ❌ "Pattern recognition and intelligent suggestions" — no built-in suggestion engine

What IS true:
- ✅ Lock-free design (no `.git/index.lock` blocking)
- ✅ First-class undo via the operation log
- ✅ Conflict-tolerant tree state
- ✅ Cleaner history-rewriting interface than git
- ✅ Anonymous branches as a first-class concept
- ✅ Git interop via colocated mode

If Joshua wants the genuine benefits, the npm `agentic-jujutsu` wrapper is optional — he can use vanilla `jj` directly and get the same underlying behavior.

---

## Migration from git workflows

| Git workflow | jj equivalent |
|---|---|
| `git checkout -b feature` | `jj new` (creates new change; no branch name needed) |
| `git add . && git commit -m "..."` | `jj describe -m "..."` (working copy auto-tracked) |
| `git rebase -i HEAD~5` | `jj rebase -d <target>` plus `jj squash` / `jj split` as needed |
| `git stash` | not needed — every change is its own thing; just `jj new` to start fresh |
| `git reflog` | `jj op log` |
| `git reset --hard` | `jj op restore` to a previous op |
| `git cherry-pick` | `jj rebase -d <target> --revisions <change>` |
| `git push origin main` | `jj git push --branch main` |
| Merge conflict | jj records the conflict, you resolve at your pace, `jj squash` when done |

---

## Tool reference

| Need | Tool |
|---|---|
| Install jj for a demo | `bash_tool` to download the binary in `/home/claude/` |
| Read jj's actual docs | `web_fetch` on `https://martinvonz.github.io/jj/latest/` |
| Compare jj behavior to git for a specific scenario | `bash_tool` running both side-by-side in `/home/claude/repo-jj` and `/home/claude/repo-git` |
| Sketch a multi-step jj migration plan | `create_file` to outputs as a markdown plan |

---

## Anti-patterns

- **Treating jj as "git with different commands"**: it's a different model. The conflict-as-state and change-vs-commit distinctions matter. Learn them.
- **Buying the npm wrapper's marketing claims**: quantum-resistance, AI conflict resolution, etc. — those weren't real. Use jj directly and you have the real benefits.
- **Switching the team without consensus**: jj is good for solo. For teams, the friction of having one jj user among git users often exceeds the benefit.
- **Skipping the operation log**: `jj op log` and `jj op restore` are the safety net. Use them.
