# Patterns, Tests and Algorithms

## P1 — Two-stage active causal learning
1. Learn essential graph G* from observational data (PC).
2. Split into chain components; for each component with undirected edges:
3. Choose a variable (design P4/P5), intervene, orient (P2/P3), update the subclass; repeat until one DAG.

## P2 — Orient by randomized experiment (ch03, §3.1)
Test Vi ⫫ Vj on experimental data only. Independent → Vi ← Vj; dependent → Vi → Vj.

## P3 — Orient by quasi-experiment (ch03, Thm 7)
With B = potential parents of Vk: P_Vi(vk | B) ≠ P(vk | B) → Vi ← Vk; P_Vi(vk) ≠ P(vk) → Vi → Vk. If both equalities hold, unidentifiable. Uses observational + experimental data.

## P4 — Optimal batch design (Algorithm 1)
For k = 1..g: for each k-subset S: if every legal combination e(S) leaves |[G]e(S)| = 1, return S. Exhaustive O(g!); precompute [G]e(Vi) for all i.
Greedy fallback: manipulate highest-undirected-degree node, delete oriented edges, repeat (may not be minimum).

## P5 — Optimal sequential design
At each step, for each candidate V compute l_i per orientation e(V)_i:
- Minimax: minimize max_i l_i.
- Entropy: maximize −Σ (l_i/L) log(l_i/L).
Tree component shortcut: l_i = node count of the i-th subtree at V.

## P6 — Approximate l_i/L by sampling (large g, h)
Random node permutation → orient each undirected edge backward along it → discard DAGs with a v-structure → dedupe → count per orientation; l'_i/L' → l_i/L as samples grow (≈ 10h samples matched exact in simulation).
