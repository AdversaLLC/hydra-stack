# The six exam scenarios as decision procedures

**Method** [U]:
1. Name the scenario.
2. Apply its primary rule.
3. Test the secondary domains: is the error classified, the delegation complete, the output schema-checked, the enforcement in code?

The scenario names and domain mapping come from the course [U]. The rules are cross-checked in the chapters.

## 1. Customer support agent (D5, with D4 and D1)

**Signals:** a refund or account limit, an upset customer, "wants a human", tool errors.

**Architecture:**
- Within policy and confident → act.
- Over the limit, no rule, or a human requested → escalate. Never approve to placate.
- The handoff carries:
  - scope ("billing dispute only");
  - account and ticket IDs verbatim;
  - confirmed findings ("duplicate charge confirmed 2026-07-18");
  - the constraint breached (85 requested vs a limit of 50);
  - what was tried.
- Transient retryable error → bounded retry. Permission or business-rule error → escalate. Two readings → one question or a stated default.
- The refund itself sits behind a code check on the limit.

**Traps:** approving to calm the customer; "please help"; escalating a retryable error or every doubt.

## 2. Code generation and review (D2, with D1)

**Signals:** a generated change, a security standard, inconsistent or noisy reviews, validation failures.

**Architecture:**
- Flag and skip lists plus severity in `system` (5-10 items).
- A schema with a severity field.
- Retry by appending the specific error, capped at 2-3, then a human.
- 2-3 blind reviewers see only the artifact; integration reconciles their findings with the original.

**Traps:** vague criteria; "try again"; unbounded retries; reviewers who see each other or the author's claims; self-review called independent.

## 3. Multi-agent research (D1, with D5)

**Signals:** N independent entities (competitors, sources), a comparison, citations.

**Architecture:**
- One parallel subagent per entity, spawned in a single turn, each with full sourceData.
- Wait for the slowest branch. Empty = a valid finding; a failure is named.
- Findings carry source, agent and date. Integration keeps a claim-to-source map and surfaces conflicts.

**Traps:** bare delegation; assuming shared history; retrying an empty result; averaging conflicts; prose integration that drops sources; running sequentially when the work is independent.

## 4. Developer productivity with Claude Code (D3)

**Signals:** "every developer", "without re-explaining", team conventions, "the same practice before this kind of work".

**Architecture:**
- Committed project CLAUDE.md, split by owner with `@import`.
- An exact prompt run by name with arguments → command.
- Know-how applied automatically for a task type (migrations) → skill.
- Per-language conventions → `paths:` rules. Personal settings → user level or `CLAUDE.local.md`.
- Must-never rules → hooks or permissions.
- An unfamiliar area → Explore, then plan mode.

**Traps:**
- CLAUDE.md copied into every folder.
- A command used for knowledge.
- A path rule where the task is the trigger: a `migrations/**` rule loads only once a matching file is touched, while a skill fires from the task.
- `allowed-tools` "restricts" (the course answer; in the docs it pre-approves).

## 5. CI/CD pipeline (D3, with D1 enforcement)

**Signals:** GitHub Actions, "before merge", "fail the build", nobody present.

**Architecture:**
- `claude -p` with precise flag and skip criteria.
- `--output-format json --json-schema`, read from `structured_output`.
- Code checks a field (`severity == "critical"`) and blocks the merge.
- Bound the run with `--max-turns`, `--max-budget-usd` and `--allowedTools`.

**Traps:** plan mode or interactive mode; keyword-grepping prose; asking the model to block the merge; default text output.

## 6. Structured data extraction (D2, with D4)

**Signals:** invoices, forms, named fields, "exact shape", formats that keep changing, nightly volume.

**Architecture:**
- A tool `input_schema`. Exam: forced `tool_choice`. Build: `auto` + `strict`, or `output_config.format`, then check the call.
- Enums for closed sets; optional fields for data that is sometimes absent.
- Two-layer validation with a bounded retry.
- Per-field confidence routing.
- Batches for overnight volume.

**Traps:** a polite "return JSON"; high temperature; every field required; rejecting the whole record; batching a live request.
