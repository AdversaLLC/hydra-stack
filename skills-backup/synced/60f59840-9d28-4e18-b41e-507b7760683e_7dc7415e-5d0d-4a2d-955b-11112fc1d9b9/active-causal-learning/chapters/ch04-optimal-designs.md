# Ch 4 — Optimal Designs of Intervention Experiments

## Core Idea
Choose manipulations to minimize either the number of manipulated variables (batch) or the remaining uncertainty after each step (sequential). Designed per chain component. Assumes intervening on Vi changes the marginal of each child Vj.

## 4.1 Sufficient interventions
- A set S is **sufficient** for [G] if, whatever the true DAG, manipulating S orients every undirected edge.
- A component with g nodes and h undirected edges has at most min{2^h, g!} DAGs.
- **Theorem 8:** any permutation of a sufficient sequence is sufficient → treat S as a set; supersets of sufficient sets are sufficient.
- Legal combination e(V1..Vk): no new v-structure or cycle, no edge oriented two ways. [G]e(S) = ∩ [G]e(Vi).
- **Minimum** sufficient set: no proper subset is sufficient.
- **Theorem 9:** the intersection of all sufficient (and of all minimum sufficient) sets is empty → no variable is mandatory; either endpoint of an edge can orient it.

## 4.2 Batch interventions (Algorithm 1)
- Optimal batch design = sufficient set of minimum size.
- Algorithm 1: for k = 1, 2, …: for every k-subset S, if |[G]e(S)| = 1 for every legal combination, return S. Exhaustive, O(g!); needs all [G]e(Vi) enumerated first (cost bounded by min{g!, 2^h}).
- Greedy heuristic: repeatedly manipulate the node with the most undirected neighbours, delete oriented edges, repeat. Not always minimum.
- Example 1: minimum sufficient sets {1,2,4}, {1,3,4}, {2,3,4}, {2,3,5}; greedy finds the same here.

## 4.3 Sequential interventions
- At step t choose the next V given the current subclass [G]e(S(t−1)).
- **Minimax:** choose V minimizing the largest resulting subclass.
- **Maximum entropy:** choose V maximizing H_V = −Σ_{i=1..M} (l_i/L) log(l_i/L), where l_i = #DAGs under orientation e(V)_i, L = Σ l_i.
- Example 1: entropies for V1..V5 = 0.9831, 1.7046, 1.7046, 1.3480, 0.4506; max subclass sizes 8, 3, 3, 6, 10 → both criteria pick V2 or V3 first.
- Criteria can disagree: class of 10 split as (1,1,1,1,1,1,1,3) vs (2,2,2,2,2) — minimax picks the second, entropy the first.
- **Tree-structured component** (Example 2): manipulating V orients every subtree hanging off V except the one where V is a leaf; with M incident edges and subtree sizes l_i, H_V has the same formula with l_i = subtree node counts. Table 7: V1 or V2 best (H = 1.0397) vs V3/V4 (0.5623).
- **Approximation for large g, h:** sample DAGs (random node permutation → orient edges backward → keep only v-structure-free DAGs, dedupe), estimate l_i/L by l'_i/L'. Alternative: randomly orient edges but then check for cycles.

## Anti-patterns
- Enumerating every DAG when g and h are large (use sampling).
- Treating greedy output as guaranteed minimum.

## Key Takeaways
- Sequential designs exploit earlier results and are more efficient than batch.
- Entropy and minimax usually agree; minimax is more conservative.

## Connects To
ch05 (empirical comparison), patterns.md (algorithms).
