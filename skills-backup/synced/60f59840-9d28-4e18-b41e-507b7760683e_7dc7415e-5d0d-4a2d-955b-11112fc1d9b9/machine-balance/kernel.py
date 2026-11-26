def mb_ladder(rows):
    """rows: (machine, level, TFLOPS, GB_per_s, basis). Returns DataFrame sorted by FLOP/byte required."""
    import pandas as pd
    df = pd.DataFrame(rows, columns=["machine", "level", "TFLOPS", "GBs", "basis"])
    df["flop_per_byte"] = df.TFLOPS * 1000.0 / df.GBs
    return df.sort_values("flop_per_byte").reset_index(drop=True)

def mb_batch_threshold(peak_tflops, bandwidth_gbs, bytes_per_weight):
    """Tokens per expert/matrix needed for a weight-streaming GEMM to be compute-bound."""
    ai_req = peak_tflops * 1000.0 / bandwidth_gbs
    return dict(flop_per_byte_required=ai_req, tokens_required=ai_req * bytes_per_weight / 2.0)

def mb_power_curve(tdp_w, floor_w, f0_ghz, peak_tf, fractions=None, v_floor=0.55):
    """DVFS model with a non-scaling floor. Returns list of dicts per clock fraction."""
    if fractions is None:
        fractions = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4)
    dyn = tdp_w - floor_w
    out = []
    for fr in fractions:
        v = v_floor + (1.0 - v_floor) * fr
        p = floor_w + dyn * fr * v * v
        out.append(dict(clock_ghz=f0_ghz * fr, clock_frac=fr, watts=p, tflops=peak_tf * fr,
                        gflops_per_w=peak_tf * fr * 1000.0 / p))
    return out

def mb_regime(flop_per_byte):
    """Coarse label for a ladder row."""
    if flop_per_byte < 20:
        return "fine-grained exchange viable"
    if flop_per_byte < 600:
        return "coarse-grained supersteps only"
    return "batch / embarrassingly parallel only"
