"""GRSL Fig. 3 — 逐场景差与分层胜率（**单栏竖版**，上下两面板）。

改成单栏竖排的理由：双栏横排版（7.16 × 2.2 in）会独占一整行宽度，
四周留白无法被文字填充；单栏竖版（3.5 in 宽）可与其他正文并排，
在同样的信息量下占用更少的版面。

输出：figures/grsl/fig3_scene_winrate.{png,pdf}
"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

import figstyle_grsl as g

M, combos, aois, aoi_split, d = g.load_matrix()
MS = np.array(d["matrix_scene"], dtype=float)

ra = [combos.index("armD_s%s" % s) for s in g.SEEDS if "armD_s%s" % s in combos]
rh = [combos.index("highresnet_cld_s%s" % s) for s in g.SEEDS
      if "highresnet_cld_s%s" % s in combos]
a_sc = np.nanmean(MS[ra, :], axis=0)
h_sc = np.nanmean(MS[rh, :], axis=0)
ok = np.isfinite(a_sc) & np.isfinite(h_sc)
a_sc, h_sc = a_sc[ok], h_sc[ok]
diff = a_sc - h_sc                      # >0 => armD 更好

win = float((diff > 0).mean())
qs = np.quantile(a_sc, [0.0, 0.25, 0.5, 0.75, 1.0])
qs[0] -= 1e-6
qs[-1] += 1e-6
lm, lw_, lx = [], [], []
for i in range(4):
    m = (a_sc >= qs[i]) & (a_sc < qs[i + 1])
    lm.append(diff[m].mean())
    lw_.append((diff[m] > 0).mean())
    lx.append(0.5 * (qs[i] + qs[i + 1]))

fig = plt.figure(figsize=(g.SINGLE, 4.35))

ax1 = fig.add_axes([0.215, 0.585, 0.755, 0.355])
ax1.axhline(0, color="#888888", linewidth=g.LW, zorder=1)
ax1.scatter(a_sc, diff, s=1.3, alpha=0.15, color=g.BLUE, edgecolors="none", zorder=2)
ax1.plot(lx, lm, color=g.RED, marker="o", markersize=3.0, linewidth=g.LW + 0.4,
         markeredgecolor="white", markeredgewidth=0.6, zorder=4, label="quartile mean")
ax1.set_xlabel("MISR scene PSNR (dB)")
ax1.set_ylabel("PSNR diff. (dB)\nMISR $-$ HN-cld")
ax1.set_xlim(10.0, 36.0)
ax1.set_ylim(-8.8, 4.6)
ax1.legend(loc="upper right", frameon=False, handlelength=1.2, borderpad=0.12,
           fontsize=6.0)
ax1.text(0.03, 0.95, "above 0: MISR better", transform=ax1.transAxes,
         fontsize=6.0, color="#555555", ha="left", va="top")
g.style(ax1)
g.panel_tag(ax1, "(a)")

ax2 = fig.add_axes([0.215, 0.105, 0.755, 0.355])
xp = np.arange(4)
ax2.bar(xp, lw_, width=0.66, color=g.PURPLE, alpha=0.85, edgecolor="white",
        linewidth=0.3, zorder=2)
ax2.axhline(0.5, color="#888888", linewidth=g.LW, linestyle="--", zorder=1)
for x, v in zip(xp, lw_):
    ax2.text(x, v + 0.022, "%.2f" % v, ha="center", va="bottom", fontsize=6.2,
             color="#333333")
ax2.set_xticks(xp)
ax2.set_xticklabels(["Q1\n(hardest)", "Q2", "Q3", "Q4\n(easiest)"], fontsize=6.0)
ax2.set_xlabel("MISR PSNR quartile")
ax2.set_ylabel("MISR win rate")
ax2.set_ylim(0, 1.02)
ax2.set_xlim(-0.6, 3.6)
ax2.text(0.98, 0.95, "overall %.3f" % win, transform=ax2.transAxes,
         fontsize=6.0, color="#555555", ha="right", va="top")
g.style(ax2)
g.panel_tag(ax2, "(b)")

g.save(fig, "fig3_scene_winrate")
print("[grsl fig3 vertical] n=%d win=%.4f mean_diff=%+.4f  figsize=%.1fx%.1f"
      % (len(diff), win, diff.mean(), g.SINGLE, 4.35))
