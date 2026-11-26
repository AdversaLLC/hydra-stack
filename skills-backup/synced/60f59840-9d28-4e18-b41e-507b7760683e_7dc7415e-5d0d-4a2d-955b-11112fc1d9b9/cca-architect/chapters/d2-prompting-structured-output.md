# D2: Prompt engineering and structured output (20%)

## Explicit criteria

- **Vague asks give unrepeatable output.** "Review for quality" changes every run. The fix is structure, not a smarter model or temperature 0. [S]
- **Three parts in the top-level `system`,** kept stable [S principle; U as the course's recipe]:
  - a **flag list** of named patterns;
  - a **skip list** naming each flag's confusable neighbour;
  - **severity** defined by consequence.
- **Use 5-10 testable items;** past about 20, each gets under-weighted. [S]
- **Testable means** a yes/no answer to "was it applied?", a stated condition, and a paired skip.
  - Good: "flag unescaped user input concatenated into a raw SQL string".
  - Bad: "check security".

## Examples and reasoning

- **Few-shot:** 2-4 contrasting pairs (say, high vs low urgency) teach shape and boundary better than a paragraph. Past about 5, gains flatten and incidental details get copied. [U numbers; docs suggest 3-5]
- **Chain of thought** pays for multi-step deduction (arithmetic, multi-condition rules, a value traced through calls); on classification it adds latency. [S]
- **On current models thinking is built in and tuned by effort,** so "add CoT" often means "raise effort". [S]

## Structured output

- **A schema constrains; prose only asks.** Use a tool whose `input_schema` is the target shape, or API structured outputs. [S]
- **`tool_choice`** [S]:
  - `auto`: may answer in text;
  - `any`: some tool, not which one;
  - `{"type": "tool", "name": ...}`: exactly that tool.
- **Exam answer:** force the named tool and add enums.
- **Build answer:** on current models forced `any`/`tool` returns HTTP 400. Use `auto` plus an instruction naming the tool plus `strict: true`, and check a call happened; or use `output_config.format` (claude-api). [S]
- **Require only what the source always has;** a required-but-absent field invites fabrication. For changing shapes, use optional fields and an `other` enum value. [S principle]
- **Check before reading:** confirm a `tool_use` block exists before reading `input`. A forced tool plus `end_turn` and no call means misconfiguration. [S]

```python
record_invoice = {
  "name": "record_invoice",
  "description": "Record fields from one invoice. Omit any field the text lacks; never guess.",
  "strict": True,
  "input_schema": {"type": "object", "additionalProperties": False,
    "properties": {
      "vendor":   {"type": "string"},
      "total":    {"type": "number"},
      "currency": {"type": "string", "enum": ["USD", "EUR", "GBP", "other"]},
      "due_date": {"type": "string", "format": "date"}},
    "required": ["vendor", "total", "currency"]}}
# Exam:  tool_choice={"type": "tool", "name": "record_invoice"}
# Build: tool_choice={"type": "auto"} + "Answer only by calling record_invoice";
#        no tool_use block -> one re-ask -> else the review queue
```

## Validation and retry

- **Validate in two layers:** schema-valid, then business-valid (for example, every action item has an owner). [S]
- **A retry stays in the conversation.** The flawed attempt remains; a new turn names the index, field, rule and what to resend (`action_items[0].owner missing`). After a tool call, the feedback is that call's `tool_result` with `is_error: true`. [S]
- **Cap at 2-3** [U], then send the last attempt plus its errors to human review, and log every attempt. [S]
- **Same failure after precise feedback?** The task, schema or input is ambiguous; fix the spec. [S]
- **Never:** restart with only the task; "try again"; raise the temperature; retry until valid.

## Message Batches [S]

- **What:** asynchronous, about half price, same quality; tools and caching work. Results arrive unordered (key by `custom_id`), within 24 h.
- **When:** nobody waits and the requests are independent: nightly reclassification, bulk extraction, offline prompt evaluation, independent reviewer passes.
- **Never** inside an agent loop or a dependent chain.

## Multi-pass review

- **Self-review in the same conversation is anchored;** independent review means fresh calls. [S]
- **Each reviewer gets only the artifact:** no other reviewer's output, and no author narrative or claims of success. [S]
- **Run 2-3 passes;** more adds cost, rarely coverage. [U]
- **Integration** gets the final findings plus the original. It reconciles, never regenerates, and gets no reasoning traces. [U]

## Exam traps

- 20+ broad categories as "thorough"; "temperature 0 fixes vagueness."
- More examples always better; CoT by default; examples as wording to copy.
- `any` picks a specific tool; "please return JSON" is enough; everything required.
- "Try again"; unbounded retries; raising temperature per retry.
- "Batches don't support tools"; 10% or 90% savings; a batch inside a live loop.
- Chained reviewers; integration fed full traces; unlimited reviewers.
