# Ch 2 — Causal DAGs and Markov Equivalence Class

## Core Idea
Formalizes graphs, the Markov property and equivalence, then proves orientation can be done separately inside each chain component.

## Key Concepts
- Graph G = (V, E). Undirected edge Vi − Vj when both (Vi,Vj) and (Vj,Vi) ∈ E; directed Vi → Vj otherwise.
- Partially directed path / cycle; a **chain graph** has no partially directed cycle.
- **Chain component**: node set connected after deleting all directed edges.
- **Chordal**: every cycle of length ≥ 4 has a chord.
- **v-structure**: head-to-head Vi → Vk ← Vj with Vi, Vj non-adjacent.
- **Markov property / factorization**: P(v1..vn) = Π P(vi | pa(vi)).
- Assumptions: faithfulness, no latent variables.
- **Markov equivalence class [G]**: all DAGs with the same Markov properties.

## Results
- **Lemma 1 (Verma & Pearl 1990):** two DAGs are Markov equivalent iff same skeleton and same v-structures.
- **Definition 2 / Lemma 3 (Andersson et al. 1997):** essential graph G* keeps an edge directed iff it has that direction in every DAG of [G]. G* is a chain graph, each component's subgraph is chordal, and Vi → Vj − Vk never appears as an induced subgraph.
- **Theorem 4:** orienting an undirected edge inside component τ cannot form a v-structure with any node W outside τ.
- **Theorem 5:** if orienting τ's edges forms no directed cycle within τ, it forms none in the whole DAG.

## Worked Example
Figure 2: four 5-node DAGs G, G1, G2, G3 share skeleton and v-structures → one class; G* (Fig. 1) has V2→V5 and V3→V5 directed, the rest undirected, one chain component {V1,V2,V3,V4}.

## Key Takeaways
- All v-structures are already found from observational data; inside a component you must not create new ones.
- Theorems 4–5 justify solving each component independently.

## Connects To
ch03 (Thm 6 keeps these properties after interventions).
