# Ch 5 — Simulation

## Setup
- True DAG = DAG (1) of Fig. 4; its essential graph (Fig. 3) has 12 equivalent DAGs; all variables binary; CPTs ~ U(0,1); 1000 runs, observational n = 1000.
- Stage 1: PC algorithm with α = 0.15 (gave the most correct essential graphs).
- Stage 2: orient via interventions; intervention significance αI ∈ {.01,.05,.10,.15,.20,.30}, intervention sample size nI ∈ {50,100,200,500}.
- Post-intervention distribution forced to differ: P'(vi) = 1 if P(vi) ≤ 0.5 else 0.
- Both orientation tests were implemented; independence test slightly more efficient; results shown use the equivalence test + max-entropy design. ~0.4 s per simulation (R 2.6.0, 2 GHz Pentium M).

## Results — Table 8 (orientation accuracy)
- λ = % correctly oriented edges overall; m = # runs where PC found the correct essential graph (~370–430 of 1000); λ' = accuracy given correct essential graph.
- Accuracy rises with nI (e.g. λ' ≈ .76–.83 at nI = 50 → ≈ .89–.97 at nI = 500).
- Best αI shrinks as nI grows: αI = .20 for nI = 50, .10 for 100, .05 for 200, .01 for 500.
- Errors from PC (wrong essential graph) are a large share of total error.

## Results — Table 9 (number of manipulated variables, nI = 100, αI = .1)
- Batch optimal and greedy: always 3.
- Random sequential: 1 (268), 2 (475), 3 (202), 4 (55) of 1000.
- Minimax: 1 (437), 2 (563). Entropy: 1 (441), 2 (559).
- Sampling approximations with h, 5h, 10h sampled DAGs converge to the exact designs as sample size grows (10h ≈ exact).

## Key Takeaways
- All sequential designs beat batch; minimax/entropy beat random.
- Small intervention samples want a looser αI; large samples want a stricter one.
