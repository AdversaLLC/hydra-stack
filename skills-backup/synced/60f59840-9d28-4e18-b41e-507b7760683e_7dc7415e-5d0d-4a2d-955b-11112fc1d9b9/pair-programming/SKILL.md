---
name: pair-programming
description: Structured AI pair programming for claude.ai. Triggers on "let's pair on this", "pair program", "drive this with me", "TDD this", "navigate me through", "help me debug step by step", "let's refactor together", "code review as we go". Provides explicit modes — Driver (Claude writes, user steers), Navigator (user writes, Claude reviews each step), Switch (alternating), TDD (test-first cycle), Mentor (Claude explains as it goes), Debug (systematic fault-finding). Built for claude.ai's actual primitives: chat conversation, bash sandbox, file editing tools. No claude-flow CLI dependency, no truth-score auto-rollback (claude.ai sandbox has no persistent checkout to roll back), just the discipline of mode-explicit collaborative coding.
---

# Pair Programming — claude.ai

Pair programming in chat is just structured collaborative coding. The original required `npx claude-flow@alpha` and described auto-rollback on truth-score failures — none of that is necessary or installable here. What IS necessary: explicit mode declaration, so the user and Claude are in the same frame.

A claude.ai chat where you're working on code is *already* pair programming. This skill makes it good pair programming.

---

## Modes

State the mode at the start of the session. Switch deliberately. Don't drift.

### Driver mode (Claude writes; user navigates)

Claude writes code. User gives high-level direction ("now add error handling for the timeout case"). Claude implements; user reviews after each step.

Discipline:
- After every meaningful chunk (function, change, test), pause and surface the choice you made
- Don't write 200 lines and ask "good?" — surface decisions in 20–50 line chunks
- Never silently change scope ("while I was at it I also refactored X") — surface scope changes for explicit consent

### Navigator mode (user writes; Claude reviews)

User writes the code (pasting, sharing files, or typing). Claude reads carefully, reviews each chunk, suggests improvements, asks clarifying questions.

Discipline:
- Read what's there, not what you'd write yourself
- Distinguish must-fix (bugs, security) from style (subjective preferences)
- One concrete suggestion per finding, not a wall of "consider also..."
- If the user's approach is different from your default but works, say "this works; here's what I'd watch for" rather than "rewrite this"

### Switch mode (alternating)

Driver and Navigator alternate at natural boundaries (end of a function, end of a test cycle, end of a logical commit). Useful for long sessions to keep both sides engaged.

Discipline:
- State the boundary before switching ("OK, you drive the next test")
- The non-driver does NOT silently take over — the driver explicitly hands off

### TDD mode

Strict test-first cycle:
1. **Red**: write a failing test that captures the next behavior
2. **Green**: write the minimum code to pass
3. **Refactor**: clean up while tests stay green
4. Repeat

Either party can drive any phase. Discipline: don't write code without a failing test pointing at it. Don't refactor with a failing test.

In claude.ai's bash sandbox, you can actually run the tests each cycle. Do.

### Mentor mode

User is learning. Claude explains the WHY of each step, not just the WHAT. Slower, more verbose, more checking-in.

Discipline:
- Don't lecture — explain in service of the immediate task
- Surface decisions as choices ("I'm using a dict here because... we could've used a list of tuples; trade-offs are...")
- Confirm understanding before moving on, but lightly — don't quiz

### Debug mode

A bug exists. Find it methodically.

Process:
1. **Observe**: what behavior is wrong, exactly? Reproducible?
2. **Hypothesize**: what's the simplest explanation that fits all observations?
3. **Test**: what would prove or disprove the hypothesis? Run that.
4. **Iterate**: result either narrows the search or invalidates the hypothesis. Either way, observe again with new info.

Discipline: don't guess-and-check by changing things. Each change should test a hypothesis. If you've made >3 changes without learning anything, stop and observe again.

Find the **first** failing step, not the symptom. The error message points at where it crashed, not where it went wrong.

### Review mode (in-flight code review)

Reviewing a PR or file together as the user works through changes. Like Navigator mode but on a finished or near-finished artifact.

---

## Session structure

### Setup (1 minute)

User states:
- Goal of the session ("add OAuth login flow")
- Mode (or "let's pick one")
- Context (relevant repo, files already in chat, language/framework)

Claude states:
- Acknowledged goal
- Selected mode
- Any clarifying question NOW (one chance, don't keep asking)

### Working (the bulk)

Hold the mode. Surface decisions. Run code in the sandbox when relevant. Use `view` and `str_replace` for files. Save artifacts to `/mnt/user-data/outputs/` when complete chunks ship.

If Claude is Driver: produce 20–50 line chunks, then pause for direction.
If Claude is Navigator: review chunks the user provides; one concrete reply per chunk.

### Mode switches

Either party calls them out: "switching to TDD now" / "let me drive the next bit". Don't drift modes silently.

### Wrap-up

End the session with:
- What was completed (concrete: function names, files, tests)
- What's open
- What's the next concrete step

If the work matters across sessions, suggest `memory_user_edits` to record the project state. (See `momentum` skill.)

---

## What got stripped from the original (1202 lines → ~150)

- **`npm install -g claude-flow@alpha`** prerequisite — dead, not needed
- **Truth-score verification with auto-rollback at threshold 0.95** — there's no persistent checkout in claude.ai's sandbox to roll back to; "verification" is just running the tests, "rollback" is `git checkout` on the user's machine
- **Real-time quality monitoring with continuous metrics** — claude.ai is turn-based; "real-time" is illusion. Each turn, Claude reviews what changed and surfaces concerns. That's the actual pattern.
- **Session persistence with auto-save / recovery / export** — sessions don't auto-save in claude.ai; if the work matters, it gets saved to files in outputs and (durable facts) to `memory_user_edits`
- **AI swarm coordination for review** — single Claude reviewing what's in the conversation
- **Configuration flag system with 30+ options** — just say the mode in chat; no config file needed
- **MCP integration for hooks** — replaced by inline workflow

What survived: the **mode definitions and discipline**. That's the actually-valuable part.

---

## Anti-patterns

- **Mode drift**: starting in TDD, drifting into "let me just write a few more functions". Stop and acknowledge the mode change explicitly, or get back to TDD.
- **Driver writing 300 lines in one turn**: surface decisions in chunks. The user can't review a wall of code.
- **Navigator that always rewrites**: review is not "show me your version". If the user's code works, comment on it; don't replace it unless asked.
- **Debug-by-changes**: don't change things hoping it fixes the bug. Each change tests a hypothesis. Otherwise you're playing whack-a-mole.
- **TDD without running tests**: the bash sandbox can run tests. Run them. "Should pass" without verification is not green.
- **Mentor mode lectures**: explain in service of the task, not in the abstract.
- **Skipping the wrap-up**: a session that ends with "and then it works" but no record of what was done is hard to resume.

---

## Working with files

claude.ai's file tools fit pair programming naturally:

| Mode | File pattern |
|---|---|
| Driver | `create_file` for new files; `str_replace` for surgical edits |
| Navigator | `view` to read what user shared; comment in chat |
| TDD | `create_file` for tests; `bash_tool` to run them; `str_replace` to make pass |
| Refactor | `view` to read; `str_replace` to change; `bash_tool` to verify tests still pass |
| Debug | `view` to read; `bash_tool` to run/instrument; `str_replace` for fixes |

Write completed work to `/mnt/user-data/outputs/` and `present_files` so the user can grab it. For long sessions, present periodically — don't make the user wait until the end to see what's been built.

---

## Tool reference

| Need | Tool |
|---|---|
| Read user's code | `view` |
| Write new code | `create_file` |
| Edit existing | `str_replace` |
| Run code/tests | `bash_tool` |
| Install language tooling | `bash_tool`: `apt-get`, `pip install --break-system-packages`, `npm install`, `cargo install` |
| Web docs lookup | `web_fetch` |
| Visualize control/data flow | `visualize:show_widget` (diagram) |
| Persist project state | `memory_user_edits` (durable facts), or save resumption notes via `momentum` skill |
| Deliver code | `present_files` on outputs |

---

## Honest scope

Pair programming in claude.ai is real and valuable for:
- Working through a specific problem with discussion
- Learning a new pattern with a knowledgeable partner
- Code review on a finished change
- TDD discipline when you're tempted to skip it
- Debugging when stuck

It's NOT a substitute for:
- A real IDE with LSP, debugger, integrated git (use VS Code / Zed / RustRover / etc. for that, with the user's preferred AI integration)
- Long sustained refactors of a large codebase (claude.ai's session is bounded; for a multi-day refactor, the user runs it locally and brings claude.ai in for specific decisions)
- Anything requiring auth'd access to the user's repo (auth lives on user's machine)

If the user's task fits one of those NOT cases, say so — point them at the right environment and offer to be the design partner instead.
