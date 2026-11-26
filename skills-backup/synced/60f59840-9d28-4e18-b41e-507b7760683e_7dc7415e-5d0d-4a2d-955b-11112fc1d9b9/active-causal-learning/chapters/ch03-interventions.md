# Ch 3 — Active Learning via External Interventions

## Core Idea
Manipulate a variable, observe how its neighbours respond, and orient the undirected edges around it. Randomized and quasi-experiments need different statistical tests.

## 3.1 Randomized experiments
- Individuals are assigned to Vi = vi with probability P'(vi); this disconnects Vi from pa(Vi).
- Post-intervention joint: P_Vi(v1..vn) = P'(vi) Π_{j≠i} P(vj | pa(vj)).
- Orientation rule (experimental data only): if Vi ⫫ Vj after intervention, orient Vi ← Vj; otherwise Vi → Vj.
- e(Vi) = the orientation obtained; [G]e(Vi) = DAGs in [G] consistent with it. Manipulating Vi splits [G] into subclasses.
- **Theorem 6:** the post-intervention graph G*e(Vi) is still a chain graph, chordal, with no induced Vj → Vk − Vl, so you can keep intervening until one DAG remains.

## Worked Example (Example 1)
Essential graph of Fig. 3 has 12 equivalent DAGs (Fig. 4). Manipulating V1 gives four orientations of V2–V1–V3 (Table 1): two leave a single DAG, two leave subclasses (2 DAGs, and 9 DAGs). Table 2 shows the full test-driven decision tree using V1, then V2, V3, V4 as needed.

## 3.2 Quasi-experiments
- Experimenter changes P(vi | pa(vi)) to P'(vi | pa(vi)) but cannot cut Vi from its parents (e.g. discount-encouraged vaccination).
- Let τ be the component, ne(Vk) neighbours of Vk, C = ch(Vk) \ τ, B = ne(Vk) \ C (potential parents of Vk).
- **Theorem 7:** if Vi is a parent of Vk, then P_Vi(vk | B) = P(vk | B); if Vi is a child of Vk, then P_Vi(vk) = P(vk).
- Orientation rule: Vi ← Vk if P_Vi(vk | B) ≠ P(vk | B) for some vk, B; Vi → Vk if P_Vi(vk) ≠ P(vk) for some vk.
- Needs both observational and experimental data (equivalence test of pre/post distributions).

## Anti-patterns
- Assuming a quasi-experiment always orients an edge: if both equalities in Thm 7 hold, the direction is unidentifiable (e.g. V1 with 3 levels where p(v2|V1=1) = p(v2|V1=2) and the intervention only shifts mass between levels 1 and 2).

## Key Takeaways
- Randomized: independence test, experimental data only.
- Quasi: distribution-equivalence test, observational + experimental data.

## Connects To
ch04 (choosing which Vi to manipulate), ch05 (both tests compared in simulation).
