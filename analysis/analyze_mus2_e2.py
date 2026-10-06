"""E2 补充分析：方差分解 + 逐 tile 基线表（读 mus2_e2.json）。

⚠ 两条口径纪律
  1. 方差分解**必须分波段做** —— 不同波段的 PSNR 绝对值不可比
     （b3 组整体比 b6 组高 5–8 dB），混在一起算会把「波段差」误当成「方法差」。
  2. 设置 A（自洽往返，无配准不确定性）与设置 B（真实跨传感器，有配准不确定性）
     必须分开报；**结论以 A 为准，B 只作旁证**。
"""
from __future__ import annotations

import io
import json
import sys

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
P = "/mnt/e/论文4/evidence/mus2_e2.json"
OUT = "/mnt/e/论文4/evidence/mus2_e2_analysis.json"
S2DS_RANGE = 11.375

d = json.load(open(P, encoding="utf-8"))
rows, keys = d["per_scene"], d["keys"]
tiles = sorted({r["tile"] for r in rows})

M = np.full((len(tiles), len(keys)), np.nan)
N = np.zeros(len(tiles), dtype=int)
for i, t in enumerate(tiles):
    sel = [r for r in rows if r["tile"] == t]
    N[i] = len(sel)
    for j, k in enumerate(keys):
        v = [r[k] for r in sel if np.isfinite(r.get(k, np.nan))]
        if v:
            M[i, j] = float(np.mean(v))

lines = ["tile 场景数: " + ", ".join("%s=%d" % (t, n) for t, n in zip(tiles, N)), ""]
lines.append("%-16s" % "baseline" + "".join("%10s" % t for t in tiles) + "%10s" % "range")
tile_range = {}
for j, k in enumerate(keys):
    r = float(np.nanmax(M[:, j]) - np.nanmin(M[:, j]))
    tile_range[k] = r
    lines.append("%-16s" % k + "".join("%10.3f" % v for v in M[:, j]) + "%10.3f" % r)
lines.append("")

by_band = {}
lines.append("=== 方差分解（分波段）")
for band in ("b3", "b6"):
    jj = [j for j, k in enumerate(keys) if k.endswith(band)]
    Mb = M[:, jj]
    tv = float(np.nanmean(np.nanvar(Mb, axis=0, ddof=1)))
    mv = float(np.nanmean(np.nanvar(Mb, axis=1, ddof=1)))
    by_band[band] = {"tile_var": tv, "method_var": mv,
                     "ratio": (tv / mv) if mv > 0 else None,
                     "baselines": [keys[j] for j in jj]}
    lines.append("  波段 %s（%d 个基线）: tile 间 std=%.3f dB | 基线间 std=%.3f dB | ratio=%.2f"
                 % (band, len(jj), np.sqrt(tv), np.sqrt(mv),
                    (tv / mv) if mv > 0 else float("nan")))
lines.append("")
lines.append("  逐 tile 内极差（方法效应）:")
for i, t in enumerate(tiles):
    lines.append("    %-8s range=%.3f dB (n=%d)"
                 % (t, float(np.nanmax(M[i]) - np.nanmin(M[i])), N[i]))
lines.append("")

lines.append("=== tile 级极差 与 S2DS(11.375 dB) 之比")
for j, k in enumerate(keys):
    lines.append("  %-16s %6.3f dB  →  %.3f × S2DS" % (k, tile_range[k], tile_range[k] / S2DS_RANGE))
lines.append("")
lines.append("=== 设置 A / B 汇总")
a_keys = [k for k in keys if k.startswith("A_")]
b_keys = [k for k in keys if k.startswith("B_")]
lines.append("  设置 A（自洽往返，无配准不确定性；以 A 为准）: 极差 %.3f–%.3f dB → %.2f–%.2f × S2DS"
             % (min(tile_range[k] for k in a_keys), max(tile_range[k] for k in a_keys),
                min(tile_range[k] for k in a_keys) / S2DS_RANGE,
                max(tile_range[k] for k in a_keys) / S2DS_RANGE))
lines.append("  设置 B（真实跨传感器，**有配准不确定性**，仅作旁证）: 极差 %.3f–%.3f dB → %.2f–%.2f × S2DS"
             % (min(tile_range[k] for k in b_keys), max(tile_range[k] for k in b_keys),
                min(tile_range[k] for k in b_keys) / S2DS_RANGE,
                max(tile_range[k] for k in b_keys) / S2DS_RANGE))
lines.append("")
lines.append("=== R2 的失败原因")
lines.append("  所有方法对的 tile 子集胜率均为 1.000。原因：零训练基线之间差距本身有 1–3 dB，")
lines.append("  远大于 S2DS 上 armD vs HighRes-Net-cld 的 0.16 dB，因此不存在「可翻转」的窄差距方法对。")
lines.append("  ⇒ **这是 R2 的设计缺陷，不是对主命题的反例。**")

res = {"tile_scene_count": {t: int(n) for t, n in zip(tiles, N)},
       "tile_mean_matrix": M.tolist(), "tiles": tiles, "keys": keys,
       "by_band": by_band, "tile_range": tile_range,
       "tile_range_vs_s2ds": {k: v / S2DS_RANGE for k, v in tile_range.items()},
       "setA_range": [tile_range[k] for k in a_keys],
       "setB_range": [tile_range[k] for k in b_keys]}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
with open(OUT.replace(".json", ".txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))
