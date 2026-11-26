# Ch 1 — Introduction

## Core Idea
Observational data can only identify a causal DAG up to its Markov equivalence class. To pick the true DAG you need external interventions; this paper makes that process active (choose what to manipulate) and optimal (manipulate as little as possible).

## Frameworks Introduced
- Two-stage active learning: equivalence class from observational data → orient remaining undirected edges by interventions, one chain component at a time.
- Two intervention types: randomized experiments and quasi-experiments.
- Two optimal designs: batch intervention and sequential intervention, using minimax and maximum-entropy criteria.

## Key Concepts
- DAG = Bayesian network; used for causal structure in bioinformatics, epidemiology, sociology, business.
- Structural learning families: Bayesian (score) methods and constraint-based methods (PC).
- Chain graphs (directed + undirected edges) represent equivalence classes (Andersson et al., 1997).
- Builds on He et al. (2005), which refined equivalence classes using domain knowledge and randomized experiments.

## Mental Models
- A randomized experiment is the gold standard but often impractical (ethics, cost); a quasi-experiment (e.g. encouraging vaccination with a discount) is weaker but feasible.

## Key Takeaways
- Interventions are expensive; the contribution is reducing how many variables you must manipulate.
- Orientation is local to chain components, which is what makes the approach scale.

## Connects To
ch02 (formal setup), ch03 (intervention mechanics), ch04 (designs).
