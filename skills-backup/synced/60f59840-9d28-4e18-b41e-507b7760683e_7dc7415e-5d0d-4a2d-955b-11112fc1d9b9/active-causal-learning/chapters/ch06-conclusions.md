# Ch 6 — Conclusions

## Core Idea
A full framework: equivalence class from observation → per-component orientation by randomized or quasi-experiments → batch or sequential optimal designs (minimax / max-entropy), with exact, approximate (sampling) and greedy solvers.

## Scalability
- Cost depends on chain-component size, not DAG size (designs run per component); per-component DAG count ≤ min{2^h, g!}.
- Real networks from the Bayesian Network Repository have small, mostly tree-shaped components: ALARM (37 nodes) has 4 components of 2 nodes; HailFinder (56) one component of 18; Carpo (60) 9 components of ≤ 7; Diabetes (413) 25 components of ≤ 3.

## Key Takeaways
- Prefer sequential designs when you can act on each result before the next experiment.
- For big components, sample DAGs instead of enumerating.
- The assumptions (faithfulness, no latents, a child's marginal shifts when its parent is manipulated) bound where the guarantees hold.
