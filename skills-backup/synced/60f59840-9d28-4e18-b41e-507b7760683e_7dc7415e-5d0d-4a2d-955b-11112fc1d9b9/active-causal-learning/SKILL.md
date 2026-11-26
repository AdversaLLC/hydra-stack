---
name: active-causal-learning
description: "He & Geng (JMLR 2008), 'Active Learning of Causal Networks with Intervention Experiments and Optimal Designs'. Use when orienting the undirected edges of a Markov-equivalence class (essential graph / CPDAG) with interventions, choosing which variables to manipulate (batch vs sequential designs, minimax vs maximum-entropy criteria), deciding between randomized experiments and quasi-experiments, or reasoning about chain components, v-structures and Bayesian-network structure learning. Note: the local file for this paper is mislabeled 'JNCC2 ... Naive Credal Classifier 2'; it is not about Java or NCC2."
metadata:
  authored_via: "claude-science"
  published_by: "agent"
  published_at: "2026-10-22T18:10:22.656Z"
  authored_by: "agent"
  authored_at: "2026-10-22T18:10:22.535Z"
  authoring_session: "df249c20-fa50-4f4d-9ba4-14b516173576"
  last_modified_by: "agent"
  last_modified_at: "2026-10-22T18:10:22.648Z"
---

# Active Learning of Causal Networks — He & Geng (JMLR 9, 2008, pp. 2523–2547)

Generated with book-to-skill (text mode, pdftotext) from the user's local PDF. Synthesized summaries, not the paper text. Source file on disk is misnamed `JNCC2: The Java Implementation Of Naive Credal Classifier 2 … .pdf`.

## How to Use This Skill

- Ask about a concept → read the matching chapter file in `chapters/` (loaded on demand).
- Need a term → `glossary.md`. Need an algorithm or test → `patterns.md`. Need a decision fast → `cheatsheet.md`.
- Answer from these files; if a detail is not here, say so instead of inventing it.

## Core Frameworks & Mental Models

1. **Observe first, intervene second.** Learn the essential graph G* (a chain graph representing the Markov equivalence class) from observational data (e.g. PC algorithm), then spend interventions only on the undirected edges that remain.
2. **Work per chain component.** Orientation inside one chain component can never create a v-structure with a node outside it (Thm 4) nor a directed cycle in the whole DAG if none forms inside (Thm 5). So every component is solved independently; cost scales with component size, not graph size.
3. **One manipulation splits the class.** Manipulating V orients the edges at V (and any edges whose reverse would create a v-structure or cycle), splitting [G] into subclasses [G]e(V). The post-intervention graph is still a valid chain graph (Thm 6), so you can repeat.
4. **Two experiment types, two tests.** Randomized experiment → V is cut from its parents; orient V–U by an independence test on experimental data only. Quasi-experiment → V's distribution changes but may still depend on parents; orient by testing pre- vs post-intervention distribution equivalence using observational + experimental data (Thm 7).
5. **Order doesn't matter for sufficiency; no variable is mandatory.** Any permutation of a sufficient set is sufficient (Thm 8); the intersection of all (minimum) sufficient sets is empty (Thm 9) — every undirected edge can be oriented from either endpoint.
6. **Sequential beats batch.** Batch design picks a minimum sufficient set up front; sequential design re-chooses after each result and needed only 1–2 manipulations in simulation where batch always needed 3.
7. **Pick the next variable by minimax or maximum entropy.** Minimax minimizes the largest surviving subclass (conservative); max-entropy H_V = −Σ (l_i/L) log(l_i/L) prefers splits into many small, even subclasses. They usually agree; they can differ.

## Chapter Index

| File | Covers |
|---|---|
| `chapters/ch01-introduction.md` | Motivation, prior work, chain graphs, contribution |
| `chapters/ch02-dags-markov-equivalence.md` | DAG notation, Markov property, Lemmas 1/3, essential graph, Thms 4–5 |
| `chapters/ch03-interventions.md` | Randomized experiments (Thm 6), quasi-experiments (Thm 7), Example 1 |
| `chapters/ch04-optimal-designs.md` | Sufficient sets (Thms 8–9), batch Algorithm 1, sequential minimax/entropy, tree case, sampling |
| `chapters/ch05-simulation.md` | PC + intervention results (Table 8), design comparison (Table 9) |
| `chapters/ch06-conclusions.md` | Summary, scalability, Bayesian Network Repository component sizes |

## Topic Index

chain component → ch02, ch04 · v-structure → ch02 · essential graph → ch02, ch03 · randomized experiment → ch03 · quasi-experiment → ch03 · sufficient set → ch04 · batch design / Algorithm 1 → ch04 · minimax / maximum entropy → ch04 · greedy heuristic → ch04 · DAG sampling approximation → ch04 · PC algorithm, significance level α → ch05 · scalability → ch06

## Supporting Files

`glossary.md` (terms) · `patterns.md` (procedures, tests, algorithms) · `cheatsheet.md` (decision tables)

## Scope & Limits

Assumes faithfulness and no latent (unmeasured) variables. Optimal designs need the number of DAGs per orientation, bounded by min{2^h, g!} per chain component (g nodes, h undirected edges); use DAG sampling when that is too large. Simulations used one 5-node binary example (R 2.6.0), so the numeric results are illustrative, not general benchmarks.
