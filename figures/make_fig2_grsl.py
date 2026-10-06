"""GRSL Fig. 2 — 排名胜率 vs 测试集 site 数（单栏宽 3.5 in）。

数据：evidence/aoi_matrix.json（精确枚举全部 C(18,k) 子集）
输出：figures/grsl/fig2_flip_curve.{png,pdf}
"""
from __future__ import annotations

import itertools

import numpy as np
import matplotlib.pyplot as plt

import figstyle_grsl as g

M, combos, aois, aoi_split, d = g.load_matrix()
arch = g.arch_vectors(M, combos)

PAIRS = [
    ("armD", "highresnet_cld", g.RED, "-", "o", "Mamba-MISR vs HN-cld"),
    ("armD", "breizhsr", g.BLUE, "--", "s", "Mamba-MISR vs BreizhSR"),
    ("highresnet_cld", "breizhsr", g.GREEN, ":", "^", "HN-cld vs BreizhSR"),
]
KS = list(range(3, 19))


def rate(a, b, k):
    dd = b - a
    c = t = 0
    for sel in itertools.combinations(dd, k):
        t += 1
        c += sum(sel) < 0
    return c / t


curves, gaps = {}, {}
for p, q, _, _, _, lab in PAIRS:
    curves[lab] = [rate(arch[p], arch[q], k) for k in KS]
    gaps[lab] = float(np.mean(arch[q]) - np.mean(arch[p]))

fig = plt.figure(figsize=(g.SINGLE, 2.45))
ax = fig.add_axes([0.185, 0.215, 0.79, 0.70])

ax.axhspan(0.20, 0.80, color="#f2dcdc", alpha=0.75, zorder=0)
ax.text(18.3, 0.50, "unstable", fontsize=6.4, color="#8c3b3b", ha="right",
        va="center", zorder=1)

for p, q, c, ls, mk, lab in PAIRS:
    ax.plot(KS, curves[lab], color=c, linestyle=ls, marker=mk, markersize=2.4,
            linewidth=g.LW + 0.3, markerfacecolor="white", markeredgewidth=0.6,
            label="%s (%.2f dB)" % (lab, abs(gaps[lab])), zorder=3)

ax.axvline(5, color="#666666", linestyle="-.", linewidth=g.LW, zorder=2)
ax.axvline(16, color="#666666", linestyle="-.", linewidth=g.LW, zorder=2)
ax.text(5.3, 1.055, "k=5", fontsize=6.0, color="#444444", ha="left", va="bottom")
ax.text(15.7, 1.055, "k=16", fontsize=6.0, color="#444444", ha="right", va="bottom")

ax.set_xlabel("Number of test sites, $k$")
ax.set_ylabel("Win rate of first method")
ax.set_xlim(2.5, 18.7)
ax.set_ylim(-0.03, 1.14)
ax.set_xticks(KS[::3] + [18])
ax.set_yticks([0, 0.2, 0.5, 0.8, 1.0])
ax.legend(loc="center left", frameon=False, handlelength=1.6,
          bbox_to_anchor=(0.02, 0.44), fontsize=5.9)

g.style(ax)
g.save(fig, "fig2_flip_curve")
st = curves["Mamba-MISR vs HN-cld"]
print("[grsl fig2] gaps: " + " ".join("%s=%+.4f" % (k, v) for k, v in gaps.items()))
print("[grsl fig2] armD vs HN: k5=%.3f  首次<=0.05 的 k=%s"
      % (st[KS.index(5)], next((k for k, v in zip(KS, st) if v <= 0.05), None)))
