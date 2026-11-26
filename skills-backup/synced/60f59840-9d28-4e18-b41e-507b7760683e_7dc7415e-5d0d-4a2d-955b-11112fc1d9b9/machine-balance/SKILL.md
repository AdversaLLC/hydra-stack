---
name: machine-balance
description: Decide whether a workload fits a piece of hardware by arithmetic intensity, not by peak FLOPS. Builds a "balance ladder" (FLOP per byte needed to stay compute-bound at every memory-hierarchy level, each row labelled vendor-peak or measured), a weight-streaming batch threshold for decode-style GEMMs, and a DVFS power-cap model with a non-scaling floor. Triggers on "can this card run X", "is it compute-bound or memory-bound", "roofline", "which chassis / slot / riser", "how many tokens per expert", "what if I cap power", or any accelerator comparison (GPU, Xeon Phi, IPU, FPGA, Cell). Not for single-thread CPU tuning.
---

# Machine Balance — the number that decides the design

Every hardware decision in a heterogeneous build reduces to the same question: at this level of the
hierarchy, how many FLOPs must I do per byte moved to keep the units busy? One table answers chassis,
riser, interconnect, batch size, and power-cap questions without argument.

## 1. The ladder

```python
L = mb_ladder([
  ("KNC", "GDDR5 per card",     2.417, 352, "peak"),
  ("KNC", "GDDR5 per card",     2.417, 175, "measured"),   # McCalpin STREAM
  ("KNC", "PCIe 2.0 x16",       2.417, 8.0, "peak"),
  ("KNC", "PCIe 2.0 x1 riser",  2.417, 0.5, "peak"),
  ("IPU", "on-die exchange",    62.5, 7800, "peak"),
])
```
Columns: machine, level, TFLOPS, GB/s, basis, **FLOP/byte required**. Sort by the last column.
Where two machines interleave, a partitioning that works on one works on the other. A row that sits
an order of magnitude off the end (a x1 riser at 4,834) is a disqualification, not a tuning problem.

**Always carry a measured row next to the peak row when a measurement exists.**

## 2. Weight-streaming batch threshold (decode GEMMs, MoE experts)

AI for `B` tokens through a weight matrix stored at `w` bytes/weight is `2B/w`. Compute-bound needs
`2B/w >= peak/bandwidth`, so `B_req = (peak_TFLOPS*1000/bandwidth_GBs) * w / 2`.

`mb_batch_threshold(tf, gbs, w)` — if `B_req` exceeds the tokens actually routed per step (1-32 in
MoE decode), the engine is starved regardless of its peak. This is how a bandwidth-rich, FLOP-poor
card beats a tensor-core GPU at small batch.

## 3. Power cap with a floor

Card power = FLOOR + DYN * (f * V(f)^2). The floor (DRAM, PHY, VRM, leakage) does not scale with core
clock. `mb_power_curve(tdp, floor, f0, peak_tf)` returns W and TF at each clock fraction.
Bandwidth-bound work loses nothing until the cores can no longer saturate memory; compute-bound work
loses linearly. **State the floor as an assumption and measure idle draw to refit.**

## Rules

- Label every row peak / measured / bound at the point of use.
- Kernel choice must be justified against the ladder BEFORE measuring; a null result on a
  bandwidth-bound kernel falsifies nothing about the programming model.
- A missing functional unit (no FP16, no matrix engine) is not on this ladder. Say so separately.
