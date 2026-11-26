# D0: Claude API foundations (modules 0-1)

## Concepts

- **Surfaces** [S]:
  - The **Messages API** (`POST /v1/messages`; SDK `create()` / `stream()`) is the base layer.
  - **Claude Code** is the agentic loop in a terminal or IDE.
  - The **Agent SDK** is that same harness as a library for your own app: a product-versus-library split, not a second engine.
  - **Claude.ai** is consumer chat.
  - Docs-only additions: the API SDK's **Tool Runner** (it loops over your tools) and **Managed Agents** (Anthropic hosts the loop and the sandbox).
- **Stateless** [S]. The model sees only the current request; the app stores and resends history in order. An API key authenticates and bills; it holds no conversation.
- **Request** [S]:
  - Required: `model`, `max_tokens`, `messages`.
  - `system` is a top-level parameter.
  - Roles are `user` and `assistant`; tool output returns as a `tool_result` block in a user message.
  - Content is a string or a list of blocks (text, image, document, tool_result).
- **Response** [S]: `content` blocks, `stop_reason`, and `usage` token counts.
- **Context window** [S]: a per-call token budget shared by system, history, tool definitions, tool results and the reply. Count tokens, not messages: one 40-page PDF can outweigh fifty short turns.
- **Growth** [S]:
  - Window use and cost grow with every resent turn. Caching makes a stable prefix cheaper but frees no window space.
  - Trimming is a deliberate app choice that can drop facts.
  - The core API never summarizes; server-side compaction is an opt-in beta.
- **`max_tokens`** is a hard cut-off, not a target length. [S]

## stop_reason → action [S]

| Value | Meaning | Do |
|---|---|---|
| `end_turn` | finished; nothing pending | return / exit loop |
| `tool_use` | tools requested; nothing ran | run all, return every result, call again |
| `max_tokens` | cut off | don't parse; raise the limit, stream, or split |
| `stop_sequence` | hit your stop string | done for that purpose |
| `pause_turn` | server-tool loop paused | resend history incl. this turn; no "continue" text |
| `refusal` | safety decline (`stop_details`) | don't resend unchanged; fall back or escalate |
| `model_context_window_exceeded` | window full | trim or compact deliberately |

The course teaches only the first three.

## Streaming [S]

- **Event order:**
  1. `message_start` (input tokens);
  2. for each content block: `content_block_start` → `content_block_delta` ×N → `content_block_stop`;
  3. `message_delta` (stop_reason, output tokens);
  4. `message_stop`.
- **Branch on `delta.type`:**
  - `text_delta` → append text;
  - `input_json_delta` → buffer `partial_json` and parse at block stop;
  - current streams also carry `thinking_delta`, `signature_delta` and `citations_delta`.
- Tool JSON can still be truncated at block stop (a `max_tokens` cut or eager input streaming), so validate it.
- Use the stream as a context manager, or the SDK's final-message helper.

## Mini-example: multi-turn

```python
history = []
def turn(text):
    history.append({"role": "user", "content": text})
    r = client.messages.create(model=MODEL, max_tokens=4000,
                               system=SYSTEM, messages=history)
    history.append({"role": "assistant", "content": r.content})  # blocks, not just text
    return r
```

Append `r.content` whole: `tool_use`, thinking and compaction blocks must go back unchanged.

## Decision rules

- **Surface from cues** [S]:
  - a script loops over the API and appends tool results → Messages API or Tool Runner;
  - your own coordinator, hooks and forking as an internal app → Agent SDK;
  - `.claude/` files, CLAUDE.md, slash commands, `-p` → Claude Code;
  - consumer chat → Claude.ai.
- **Steer at inference time** (system, tools, context). Fine-tuning is out of exam scope. [S]
- **Low variability:** the course says temperature near 0, never raised on retries [U]. The newest models reject non-default sampling, so use schemas, examples and effort (claude-api) [S]. Temperature 0 never guaranteed identical output.
- **Coordinator on a stronger model,** cheap subagents on a smaller one. [U]

## Exam traps

- `role: "system"` for the system prompt; `role: "tool"` for tool output.
- Context measured in messages; "the API summarizes old turns" or "bills only the newest message."
- `end_turn` or `tool_use` read as "the tool ran."
- Blaming a model memory cap or temperature for a forgotten fact.
- Claude Code chosen for an internal orchestration app (→ Agent SDK).
- Parsing every stream delta as JSON.
