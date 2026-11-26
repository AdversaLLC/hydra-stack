# D1: Agentic architecture and orchestration (27%)

## 1. The agentic loop

- **Loop only when needed.** Loop when the next step depends on the last result; a one-shot task gets one call. [S]
- **Exit on `end_turn`.** A hard cap (course: 20-50 iterations [U]) is a backstop; hitting it is a failure. [S]
- **Handle the whole response.** It can hold text plus several `tool_use` blocks [S]:
  - append the whole `content`;
  - run every call, concurrently if they are independent;
  - return every `tool_result`, keyed by `tool_use_id`, in **one** user message;
  - make one follow-up call.
  - A tool that throws still answers its id with `is_error: true`.
- **Validate tool input before any side effect.** [S]
- **Four anti-patterns:** no ceiling; unvalidated input; ad hoc trimming of history; looping a one-shot task. [S]

```python
def agent(client, messages, tools, system, cap=25):
    for _ in range(cap):                        # backstop, not the exit
        r = client.messages.create(model=MODEL, max_tokens=16000,
                                   system=system, tools=tools, messages=messages)
        messages.append({"role": "assistant", "content": r.content})  # whole turn
        if r.stop_reason in ("end_turn", "stop_sequence"):
            return r
        if r.stop_reason == "tool_use":         # all results in one user turn
            calls = [b for b in r.content if b.type == "tool_use"]
            messages.append({"role": "user", "content": [run_tool(b) for b in calls]})
            continue
        if r.stop_reason == "pause_turn":       # server tools paused: resend as is
            continue
        if r.stop_reason == "max_tokens":       # truncated; tool input may be partial
            raise Truncated(r)                  # raise the limit, stream, or split
        if r.stop_reason == "refusal":
            return escalate(r, r.stop_details)  # never resend unchanged
        raise UnknownStop(r.stop_reason)
    raise CapReached(messages)                  # failure: route to a human

def run_tool(b):
    try:
        out = TOOLS[b.name](**validate(b.name, b.input))   # schema + business checks
        return {"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(out)}
    except ToolError as e:                      # answer the id, never drop it
        return {"type": "tool_result", "tool_use_id": b.id, "is_error": True,
                "content": json.dumps(e.as_dict())}  # category, retryable, message
```

- **Claude Code is this loop.** Its ceilings: `--max-turns`, `--max-budget-usd`, and subagent `maxTurns`. [S]
- **Tool calls in one turn are not parallel subagents** [S]. Tool calls run in one shared context and save round trips; subagents are separate instances with their own contexts and save wall-clock time. In Claude Code, parallel subagents are several `Agent` calls (formerly `Task`) in one turn.

## 2. Decomposition

- **Decompose for separable subgoals** with checkable results, not for prompt length. [S]
- **Three shapes** [S; names U]:
  - **Sequential** ("prompt chaining"): steps known in advance (invoices, ETL).
  - **Adaptive** ("dynamic decomposition"): a planning call writes this instance's steps (migrations, audits, debugging). Costlier and harder to debug.
  - **Hybrid**: fixed stages with adaptive substeps; the usual production shape.
- **When a step fails** [S]:
  - hard dependency → halt and escalate;
  - transient error → bounded retry;
  - plan invalidated → re-plan from the failure point.
  - Never feed invalid partial output forward.

## 3. Coordinator and subagents

- **The coordinator owns** the goal, decomposition, delegation, reconciliation and "done". Subagents do one narrow job with fewer tools. Communication is hub and spoke; subagents never message each other. [S]
- **Fresh subagents start blind.** They see none of the coordinator's conversation; a bare "review this code" is a context-free failure. [S]
- **Brief fields** [S principle; names U]:
  - **source**: where the task sits;
  - **sourceData**: the content itself, or paths the subagent can open;
  - **role**;
  - **constraints**: flag, ignore, files owned, budget;
  - **return shape**.
  - Mark inputs confirmed or speculative, so guesses don't become facts.
- **Subagents return findings,** not transcripts. [S]
- **Claude Code nuances** [S]:
  - `fork` subagents inherit the conversation;
  - fresh ones share the filesystem, so a path works and "as discussed" doesn't;
  - CLAUDE.md loads into every subagent except Explore.

```text
Task 2 of 3: security pass on PR 482. The coordinator merges three reviews.
Inputs: /repo/src/auth/session.py lines 40-120; diff at /tmp/pr482.diff.
Confirmed: tokens are HS256 JWTs. Speculative: refresh may skip the expiry check.
Role: application-security reviewer. Read-only; at most 15 turns.
Flag: auth bypass, missing signature/expiry checks, hard-coded secrets. Ignore: style.
Return: STATUS done|empty|failed, then findings [{claim, file:line, severity, evidence}].
```

## 4. Parallel spawning

- **Spawn independent subtasks in one turn.** Wall-clock time falls from the sum to the slowest branch; total work is unchanged. [S]
- **Failure vs empty** [S]:
  - **Failure** (it errored): name the missing branch, then retry it, go partial, or escalate, and say so in the synthesis.
  - **Empty** (it succeeded, found nothing): a valid finding; report it, don't retry it.
- **Cap fan-out** under rate limits. [S]
- **Independent includes disjoint files:** parallel writers collide on disk, so use `isolation: worktree` or run sequentially. [S]

## 5. Enforcement: gates and hooks

- **Prompts shape likelihood; code decides possibility.** Ask: "what if it does this wrong 3% of the time?" If unacceptable, use code. Deploys, refunds, outbound email and transfers all need a gate. [S]
- **A gate has three parts** [S]:
  - deterministic checks your code runs (tests, schema, approval);
  - a structured handoff payload;
  - block and escalate on failure. Never "continue with a note", and never use another model's opinion as the gate.
- **A hook fires per tool call or event; a stage gate is ordinary code** deciding whether the next stage is reachable. [S]

```python
def deploy_gate(s):
    failed = [k for k in ("tests_passed", "schema_valid", "human_approved") if not s.get(k)]
    return ({"status": "blocked", "failed_checks": failed, "next": "escalate"}
            if failed else {"status": "open"})        # deploy() runs only when open
```

- **Hook points** [S]:
  - **PreToolUse**: should this run at all? (prevent)
  - **PostToolUse**: was the result okay? (inspect, normalize, flag; it can't undo)
  - **Stop**: prove completion.
  - A log-only hook is observability. Config syntax: d3. Course verdict names → doc fields: `traps.md`.
- **`prompt` and `agent` hook handlers are model judgment:** reviewers, not gates. [S]

## 6. Session strategy [S]

| Need | Choose | Claude Code / Agent SDK |
|---|---|---|
| same task, full fidelity | resume | `--resume`, `--continue`; SDK resume by session id |
| try an alternative, keep the original | fork | `--fork-session`, SDK `fork_session` (new id, history only, files not branched) |
| uncontaminated run | fresh + isolation | `claude -p`, a fresh subagent, skill `context: fork` (no history despite the name) |
| new task, or stale context | fresh + summary | a curated handoff; compaction within a session |

- **Signal phrases** [U]:
  - "continue where we left off", "targeted re-analysis of changed files" → resume, then re-check those files;
  - "compare two approaches" → fork;
  - "days old", "codebase changed significantly" → fresh with a summary.
- **Branches that see each other are a broken fork.** Forks isolate history, not the disk. The Messages API has no resume or fork parameters. [S]

## Exam traps

- A fixed iteration count as the exit; "looping is always safer"; unvalidated tool input.
- A subagent that "inherits" history; a long role prompt with no content; subagents messaging each other.
- Average or fastest branch time; aborting or retrying all over one error; empty treated as failure; a failed slot dropped.
- A forceful prompt or more `max_tokens` as a gate; retrying the check forever.
- A log-only hook as enforcement; PostToolUse for "never"; a hook where a stage gate belongs.
- "Parallel subagents" as the answer about one response's `content` array.
