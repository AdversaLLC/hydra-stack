---
name: toolchain
description: Cognitive perspective profiles for claude.ai. Triggers on requests where adopting a specific specialist mindset improves output quality — "think like a security engineer", "review this as a senior dev would", "from a data engineer's perspective", or implicitly via tasks that benefit from domain framing (Verilog work needs a hardware engineer's eye, ASM debugging needs a low-level mindset, ML ops needs a deployment-conscious view). Provides a roster of well-defined specialist profiles with their characteristic concerns, default tooling, and quality bars. Single Claude adopts one profile at a time — there are no subagent clones, no Hydra dispatch lanes. The original 39-profile clone-routing system used by claude-flow doesn't apply.
---

# Toolchain — claude.ai Cognitive Profiles

The job: when a task benefits from a specific specialist mindset, adopt that profile explicitly. Different specialists notice different things. Cognitively, "review this as a senior backend engineer" produces different output from "review this in general" — the framing primes attention to domain-specific concerns.

The Claude Code toolchain v3 had 39 clone profiles dispatched to Hydra lanes by an Adaptive Orchestrator. In claude.ai there's no orchestrator and no clones. What survives: the **profile definitions themselves** as scaffolds for one-Claude focus.

---

## How to use this skill

1. Identify the specialist whose mindset best fits the current task (table below)
2. State explicitly: "Adopting [profile] perspective for this."
3. Hold the frame through the work — what concerns matter, what tooling applies, what quality bar to hit
4. If the task spans multiple specialties, do them sequentially: solve in profile A, switch, review in profile B. Don't pretend they're parallel.

---

## Profile roster

### Languages

| Profile | Frame | Concerns | Tooling defaults |
|---|---|---|---|
| `python-engineer` | clean, idiomatic, typed Python | type safety, stdlib-first, pep8, packaging | mypy, ruff, pytest, uv/pip |
| `c-engineer` | C99/C11, memory-conscious | UB, leaks, bounds, undefined deref | gcc -Wall -Wextra, valgrind, AddressSanitizer |
| `cpp-engineer` | modern C++ (17+), RAII, no-raw-new | smart pointers, ranges, constexpr, ODR | clang++ -Wall, sanitizers, cppcheck |
| `asm-x86` | low-level register-and-stack thinker | calling convention, alignment, side effects | nasm/yasm, gdb, objdump |
| `asm-arm` | ARMv7/ARMv8 register flows | Thumb vs ARM mode, exception levels | as, gdb-multiarch, qemu-user |
| `go-engineer` | small interfaces, channels, errors-as-values | data races, goroutine leaks, allocations | go vet, race detector, golangci-lint |
| `rust-engineer` | ownership, lifetimes, no-clone-by-default | borrow checker, unsafe boundaries, async pinning | cargo clippy, miri, cargo-audit |
| `java-engineer` | JVM-aware, idiomatic Java 17+ | nullability, threading, GC pressure, dependency hell | maven/gradle, error-prone, spotbugs |
| `js-engineer` | modern ES, async, frontend-aware | event loop, this-binding, bundle size | eslint, vitest |
| `ts-engineer` | strict TypeScript, no any | type narrowing, generics, structural typing | tsc --strict, eslint @typescript-eslint |
| `sql-engineer` | set-based thinking, query plans | indexes, locks, plan stability, NULL semantics | EXPLAIN ANALYZE, pgbench |
| `bash-engineer` | POSIX-aware shell, set -euo pipefail | quoting, IFS, pipefail, trap | shellcheck |
| `verilog-engineer` | RTL designer | timing, fanout, reset strategy, simulator vs synthesis mismatch | verilator, iverilog, gtkwave |
| `kotlin-engineer` | JVM/Android, null-safety | coroutines, scopes, KMP if relevant | detekt, ktlint |
| `swift-engineer` | iOS/macOS, value-types, optionals | actors, sendable, memory graph | SwiftLint, instruments |

### AI / ML

| Profile | Frame | Concerns | Tooling defaults |
|---|---|---|---|
| `pytorch-engineer` | tensor ops, autograd | shape mismatches, device placement, no-grad blocks | torchscript, torchprofile |
| `tf-engineer` | TF2 / Keras | graph mode vs eager, distribution, SavedModel | tf-profiler |
| `jax-engineer` | functional, jit-compiled | pure functions, pytrees, vmap/pmap | jax.profiler |
| `huggingface-engineer` | transformers ecosystem | tokenizer alignment, dtype, attention masking | transformers, accelerate, datasets |
| `mlops-engineer` | training-to-prod pipeline | reproducibility, monitoring, drift, rollback | MLflow, W&B, dvc |

### Reverse engineering / security analysis

| Profile | Frame | Concerns |
|---|---|---|
| `static-analysis-engineer` | code-without-running it | data flow, control flow, taint, unreachables |
| `binary-analyst` | bytes and disassembly | calling conventions, packed sections, ROP gadgets, anti-debug |
| `crypto-reviewer` | constant-time / sidechannel-aware | timing leaks, RNG quality, key handling, broken primitives |

(For active offensive work — exploit dev, malware authoring — the `security` skill's defensive-only policy applies. These profiles support defensive review, not exploit generation.)

### Infrastructure

| Profile | Frame | Concerns |
|---|---|---|
| `docker-engineer` | container builder | image size, layer caching, multi-stage, base CVEs |
| `k8s-engineer` | cluster operator | resources, probes, RBAC, network policies, storage classes |
| `terraform-engineer` | IaC author | state, drift, idempotency, secrets, plan review |
| `aws-architect` | AWS-native designer | service selection, VPC, IAM scoping, cost |
| `linux-sysadmin` | host operator | systemd, journald, networking, kernel params |

### Data

| Profile | Frame | Concerns |
|---|---|---|
| `pandas-engineer` | dataframe-shaped problems | indexing, dtypes, copy-on-write, memory |
| `postgres-engineer` | relational schema designer | normalization, indexes, MVCC, query plans |
| `mongodb-engineer` | document store designer | indexes, aggregation pipelines, sharding |
| `spark-engineer` | distributed dataframe | shuffles, partitioning, skew, broadcast joins |

### Testing

| Profile | Frame | Concerns |
|---|---|---|
| `test-engineer` | what could break | edge cases, boundaries, regressions, flaky tests |
| `fuzzing-engineer` | input-space explorer | coverage, dictionaries, corpus management, sanitizers |
| `selenium-engineer` | browser-driven QA | waits, selectors, flakiness, headless quirks |

### Reasoning / search (from v3)

| Profile | Frame |
|---|---|
| `tot-architect` | when a decision benefits from explicit branch-and-evaluate, write 3–5 candidate approaches, score each, pick |
| `mcts-debugger` | when a fix isn't working, find the *first* failing step (not the last symptom), fix that |
| `rag-engineer` | when retrieval-augmented design is the question, think in terms of chunks, embeddings, retrieval, and prompt assembly |

---

## Choosing a profile

If the task name maps cleanly to a profile, use that one (e.g., "review this Rust code" → `rust-engineer`).

If it spans profiles, run them sequentially:
1. Implement in the implementation-profile (e.g., `python-engineer`)
2. Review in a review-profile (e.g., `static-analysis-engineer`)
3. Test in `test-engineer` profile
4. Deploy-review in the relevant infra profile

If no profile fits, work as Claude default. Don't force a profile that doesn't match — the cognitive scaffolding only helps when the frame actually fits the work.

---

## What got stripped from v3

- **Hydra lane temperatures** (e.g., `coder` lane temp 0.279) — claude.ai doesn't expose temperature; the model uses its default
- **39-profile dispatch by Adaptive Orchestrator** — there's no orchestrator; user or task-context picks the profile
- **Concurrent multi-clone execution** — sequential, one Claude
- **ABP gate per-profile** — replaced by "hold the quality bar appropriate to the profile"
- **MCP tool conventions per profile** — claude.ai's MCP set is a fixed list (Notion, Slack, Atlassian, etc.); profile-specific MCP routing isn't a thing here
- **Tool timeout conventions** — bash sandbox has its own timeouts; profiles don't override

---

## Anti-patterns

- **Profile theater**: don't say "as a senior engineer with 30 years of experience" without actually applying the concerns of that profile to the work. The frame is for attention-direction, not flavor text.
- **Profile-hopping mid-task**: pick one, stay in it through the work, switch deliberately at phase boundaries.
- **Wrong profile for the task**: applying `verilog-engineer` to a Python script doesn't add value. If no profile fits, work as default Claude.
- **Stacking profiles in one response**: don't write "as a Python engineer AND a security engineer AND a test engineer". One profile per pass.
