# Cheatsheet

| Situation | Do this |
|---|---|
| Can randomize the treatment | Randomized experiment; orient with independence test on experimental data (P2) |
| Can only nudge behaviour | Quasi-experiment; equivalence test with obs + exp data (P3) |
| Must fix all experiments up front | Batch design, Algorithm 1 (P4) |
| Can adapt after each result | Sequential design, minimax or entropy (P5) — fewer manipulations |
| Component too big to enumerate | Sample DAGs to estimate l_i/L (P6) |
| Want guaranteed small worst case | Minimax |
| Want most even split / lowest expected uncertainty | Maximum entropy |

| Fact | Value |
|---|---|
| DAGs per component | ≤ min{2^h, g!} |
| Mandatory variables to manipulate | none (Thm 9) |
| Order of a sufficient set | irrelevant (Thm 8) |
| Example 1 manipulations | batch 3 always; minimax/entropy 1–2 |
| Best αI by intervention sample nI | 50→.20, 100→.10, 200→.05, 500→.01 |
