---
name: workflow-automation
description: Multi-step workflow design and execution within claude.ai. Triggers on "automate this", "build a workflow", "make a pipeline", "do these N steps in order", "every time X happens do Y", "create a reusable process". Designs and executes sequential workflows in one Claude session, drafts external automation specs (n8n / Zapier / GitHub Actions / cron) for the user to deploy themselves. Single-instance, no orchestrator daemon, no agent pool, no persistent workflow state machine — claude.ai sessions don't run between turns. The Claude Code version with claude-flow workflow registry and 60+ agent pool doesn't apply.
---

# Workflow Automation — claude.ai

The job: design and run multi-step workflows. Two flavors:

1. **In-session sequential workflow** — Claude executes the steps now, in this conversation, using available tools.
2. **External automation spec** — Claude designs the workflow as a config the user deploys to a real automation runtime (n8n, Zapier, GitHub Actions, Make, Temporal, cron+systemd, etc.).

claude.ai itself isn't an automation runtime. It doesn't run between user turns. It doesn't trigger on schedules. For "every Monday at 9am send a report" workflows, the design happens here; the execution happens on the user's chosen runtime.

---

## Choosing the flavor

| Workflow shape | Flavor |
|---|---|
| User wants the result now, all steps fit in one session | In-session sequential |
| User wants this to keep happening, with no claude.ai involvement after setup | External automation spec |
| User wants a "template" they can re-run later | External automation spec (with optional in-session demo run) |
| User wants Claude to orchestrate humans (assign tasks, follow up) | This is a project-management tool's job; design the workflow, deploy in Asana/Linear/Notion |

Don't pretend in-session execution can substitute for scheduled automation. The conversation ends; the workflow doesn't keep running.

---

## In-session sequential workflow

### Design

Lay out the steps explicitly:

```
Step 1: <action> using <tool>; depends on: <inputs>; produces: <outputs>
Step 2: <action> using <tool>; depends on: Step 1's output
...
Step N: <action> using <tool>; produces: <final deliverable>
```

State explicitly which steps have side effects (write a file, send an email via MCP, post to Slack via MCP). Side-effect steps should pause for user confirmation if the workflow is non-trivial — don't fire 12 emails unsupervised.

### Execution

Run the steps in order. Print the step header, do the work, show the result, proceed.

If a step fails:
- Stop the workflow
- Report what failed and why
- Show what's been completed already
- Ask whether to retry, skip, or abort

Don't silently swallow failures and continue.

### Final report

After the last step, produce a summary:
- What was done (list, with outputs)
- What's now in `/mnt/user-data/outputs/` if anything
- What the user should do next (if the workflow has a next phase)
- Any side-effects that occurred (emails sent, Slack posts made, etc.)

---

## External automation spec

When the workflow needs to keep running on its own:

### Pick the right runtime

| User context | Suggested runtime |
|---|---|
| User has a GitHub repo and wants triggers on push / PR / schedule | GitHub Actions |
| User wants a visual workflow with many SaaS integrations | n8n (self-hosted) or Make/Zapier (managed) |
| User has Linux box and wants cron + scripts | systemd timers + bash/python |
| User runs Temporal, Airflow, Prefect already | use that |
| User just wants "do this in Notion when X happens" | Notion automations + Zapier/Make bridge |
| User wants serverless event-driven | AWS EventBridge + Lambda, or Cloudflare Workers Cron Triggers |

### Produce the spec

For each runtime, output the actual config the user deploys. Don't describe — produce.

**GitHub Actions example:**

```yaml
# .github/workflows/weekly-report.yml
name: Weekly Report
on:
  schedule:
    - cron: '0 9 * * 1'  # Mondays 9am UTC
  workflow_dispatch:

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          python scripts/generate_report.py
          # ...
      - uses: actions/upload-artifact@v4
        with:
          name: weekly-report
          path: report.pdf
```

**n8n** (export as JSON workflow): produce the JSON or the visual node graph as a list.

**cron + systemd timer**: produce both the `.service` and `.timer` unit files.

**Cloudflare Workers Cron Trigger**: produce the `wrangler.toml` cron configuration plus the worker script.

Always include:
- The trigger (schedule, event, webhook)
- The actions
- Any secrets/env vars the user needs to configure (don't include real secrets)
- A test invocation the user can run to validate setup
- Notes on common failure modes

### Deployment instructions

After the spec, give the user the install commands or click-paths. "Add this YAML to `.github/workflows/`, commit and push. Set the `OPENAI_API_KEY` secret in repo settings." Concrete and ordered.

---

## Common workflow patterns

### Daily / weekly digest

Pattern: aggregate from N sources, summarize, deliver to a channel.

In-session demo: run once now to validate. External spec: GH Actions cron + Slack webhook.

### Issue-tracker triage

Pattern: when a new issue lands, label it and assign based on content.

External spec: GitHub Actions on `issues.opened` event, calling Claude API or rule-based labeler.

### Document approval pipeline

Pattern: doc lands → reviewer notified → on approve, publish; on reject, send back.

This is what Notion / Asana / Linear are built for. Claude designs the workflow inside that tool — don't reinvent.

### Data pipeline (extract → transform → load)

Pattern: pull from source, clean, push to destination, alert on failure.

In-session: claude.ai's bash sandbox runs the demo on a sample. External: real ETL tool (Airbyte, Fivetran, dbt, custom Airflow DAG).

### Human-in-loop approval

Pattern: every Nth step requires a human ack before continuing.

In-session: pause and ask via `ask_user_input_v0`. External: Slack approval workflow, webhook back into the runtime.

---

## What got stripped from v1

- **claude-flow workflow registry** — that's a Claude Code feature; here we don't have a registry of saved workflows that persist between sessions. If the user wants to reuse a workflow design, save it as a markdown file and re-share next session.
- **60+ agent pool spawn** — no agents
- **Topology coordination (hierarchical, mesh, ring)** — these are SwarmOrchestration concepts that assumed multiple agents; here it's one Claude doing steps in order
- **Real-time orchestration daemon** — claude.ai is turn-based; nothing runs between turns

---

## Anti-patterns

- **Pretending claude.ai schedules**: it doesn't. "Every Monday at 9am" requires an external runtime.
- **Stateful workflows assuming Claude remembers between sessions**: Claude doesn't. State persists via `memory_user_edits` (slow updates, durable facts) or via files the user re-uploads. Don't design workflows that expect Claude to know what happened last Tuesday.
- **Over-automating**: some workflows are better as a checklist the user runs by hand. Automation has setup + maintenance cost; for things that happen 3 times a year, manual is fine.
- **Underspecifying secrets / credentials**: every external workflow needs the user to configure auth. Surface that explicitly in the deployment instructions.
- **Skipping the test run**: don't ship an external workflow spec without a test invocation that proves it works.

---

## Tool reference

| Need | Tool |
|---|---|
| In-session multi-step execution | claude.ai's full toolset, sequential |
| Schedule / config files for external runtime | `create_file` to outputs |
| Look up runtime docs (GH Actions syntax, n8n nodes, etc.) | `web_fetch` |
| Sample data / test inputs | `bash_tool` to generate or fetch |
| User confirmation between side-effect steps | `ask_user_input_v0` |
| Visualize the workflow graph | `visualize:show_widget` (diagram module) |
| Save the spec for the user | `create_file` to outputs, `present_files` |
| Persist that "user has a daily-digest workflow" across sessions | `memory_user_edits` one-liner |
