# D4: Tools and MCP (18%)

## The tool contract

- **A tool is a JSON description** in `tools[]`, not code [S]:
  - `name` reads like a function (`get_weather`, not `tool_3`);
  - `description` does the routing;
  - `input_schema` is JSON Schema, with per-property descriptions and format examples, and `enum` for closed sets.
- **Claude proposes; your code executes.** `stop_reason: "tool_use"` means nothing has run. The app owns execution, retries, permissions, side effects and error shape. Exception: server tools (web search and fetch, code execution) and the API's MCP connector run on Anthropic's side. [S]
- **A strong description** says what, when, when not, and names the most confusable tool. [S]
- **Misrouting:** rewrite both descriptions with an explicit boundary, then shrink the active list (course: about 4-5 per role [U]). A bigger model or more tokens is not the fix. Claude Code defers MCP schemas behind tool search, but names still take context. [S]

```text
search_code: Search this repository's source for a symbol or regex. Use for definitions,
call sites and config keys. Not for product docs or how-to questions: use search_docs.
```

## Built-in vs custom vs MCP [S]

| Need | Choose |
|---|---|
| local files, repo, shell | built-in: Read, Write, Edit, Grep, Glob, Bash |
| deterministic logic you own | custom tool (API: local function; Claude Code: small MCP server or script) |
| external system (Jira, GitHub, browser) | MCP server |

- **Search and edit tools:**
  - Grep searches contents; Glob matches paths; Write replaces a whole file.
  - Edit swaps an exact `old_string`. It fails unless the string is unique (or `replace_all` is set), which proves the text was found and drops nothing.
- **Routing among built-ins is description-driven,** not a fixed priority. An MCP server for local search adds a process for nothing.

## MCP [S]

- **An open protocol.** Client and server share discovery, call shape and error shape; a server wraps the real API rather than replacing it.
  - USB-C analogy: the port is the protocol, not one server.
  - The chain: Claude Code → MCP client → MCP server → external system.
- **"Claude can't do X externally" means a missing connection,** not missing intelligence. `claude mcp add` writes launch config with no retraining; tools are discovered at runtime (`claude mcp list` checks them).
- **Primitives:**
  - **tools**: model-invoked actions, often with side effects; read-only tools exist (`readOnlyHint`);
  - **resources**: read-only context addressed by URI and app-controlled; `@server:` mentions in Claude Code;
  - **prompts**: templates, run as `/mcp__server__prompt`.
  - A read-only board snapshot is a resource.

## Error results

- **Where failures go:** tool execution failures go inside the result (`isError: true` in MCP, `is_error: true` on an API `tool_result`). Malformed requests and unknown tools are JSON-RPC protocol errors. [S]
- **Course fields** [U as fields]: `errorCategory`, `isRetryable`, `message` (for humans and logs) and `context` (endpoint, attempt, field). Only `isError` is protocol; the rest is a convention in content text or `structuredContent`. [S]
- **Branch on category and retryability,** never on the message prose. [S]

| Category | Retryable | Action |
|---|---|---|
| transient (timeout, 503, lock) | yes | bounded retry with backoff |
| validation (bad or missing field) | not as is | fix the input from `context`, retry once; else escalate or skip |
| permission | no | escalate; the same credentials fail the same way |
| business rule (limit, policy) | no | escalate or abort |

- **Empty is success:** `isError: false` with an empty list. An outage must never look empty. [S]

```json
{"isError": true,
 "content": [{"type": "text", "text": "{\"errorCategory\": \"permission\", \"isRetryable\": false, \"message\": \"Token lacks issues:write on acme/api\", \"context\": {\"endpoint\": \"POST /repos/acme/api/issues\", \"attempt\": 1}}"}]}
```

## Configuration and secrets [S]

- **Scopes:**
  - local (the `claude mcp add` default): private, in `~/.claude.json` under the project;
  - project (`--scope project`): `.mcp.json` at the repo root, committed, approved once per user;
  - user: all your projects.
  - For the same server name: local > project > user.
- **Secrets:** reference them as `${VAR}` or `${VAR:-default}`; each developer or CI runner sets the value. Never put a literal token in a committed file.
- **Restrict exposed tools** with permission rules (`mcp__server__tool`), subagent `tools` / `mcpServers`, or `--allowedTools` / `--disallowedTools`. A `tools` key in the server entry is course-only [U].

```json
{"mcpServers": {"jira": {"command": "npx", "args": ["-y", "<jira-mcp-package>"],
  "env": {"JIRA_API_TOKEN": "${JIRA_API_TOKEN}"}}}}
```

## Exam traps

- "A more capable model" or more tools for misrouting.
- `tool_use` read as "Claude ran the tool."
- MCP for local file search; built-ins picked by a fixed priority.
- Fine-tuning as the reason a new MCP task now works; the USB-C port read as one server.
- Everything from a server treated as a tool.
- Retrying any `isError`; zero matches treated as an error; branching on prose.
- A literal token in `env`; "user scope always wins."
