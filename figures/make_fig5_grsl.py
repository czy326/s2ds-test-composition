"""GRSL Fig. 4 — MuS2 外部复现（**单栏竖版**，上下两面板）。

与 Fig 3 同理：单栏竖排可与其他正文并排，比跨栏横排占用更少版面。

⚠ 图号由 tex 中的插入顺序决定（按正文首次引用顺序编号）：
MuS2 复现在 §III-E 首次引用，早于 §III-F 的 valid 占比 ⇒ 本图是 **Fig. 4**。
输出文件名用 fig4_*，与图号保持一致。

输出：figures/grsl/fig4_mus2.{png,pdf}
"""
from __future__ import annotations

import json

import numpy as np
import matplotlib.pyplot as plt

import figstyle_grsl as g

d = json.load(open(g.EV / "mus2_e2_analysis.json", encoding="utf-8"))
M = np.array(d["tile_mean_matrix"], dtype=float)
tiles, keys, N = d["tiles"], d["keys"], d["tile_scene_count"]
S2DS = 11.375

INT = ["nearest", "bilinear", "bicubic"]
IC = {"nearest": g.ORANGE, "bilinear": g.GREEN, "bicubic": g.BLUE}
sel = [keys.index("A_%s_b6" % m) for m in INT]
Mb = M[:, sel]

fig = plt.figure(figsize=(g.SINGLE, 5.0))

ax1 = fig.add_axes([0.185, 0.585, 0.785, 0.355])
x = np.arange(len(tiles))
w = 0.26
for j, m in enumerate(INT):
    ax1.bar(x + (j - 1) * w, Mb[:, j], width=w, color=IC[m], edgecolor="white",
            linewidth=0.25, label=m, zorder=2)
ax1.set_xticks(x)
ax1.set_xticklabels(["%s\n%d" % (t, N[t]) for t in tiles], fontsize=5.4)
ax1.set_ylabel("Self-consistent PSNR (dB)")
ax1.set_xlabel("MGRS tile (scene count)")
ax1.set_ylim(24, 37.5)
ax1.legend(loc="upper left", frameon=False, ncol=3, handlelength=0.8,
           columnspacing=0.6, borderpad=0.12, fontsize=5.8)
g.style(ax1)
g.panel_tag(ax1, "(a)", y=1.025)

ax2 = fig.add_axes([0.185, 0.105, 0.785, 0.355])
A = [d["tile_range"][k] for k in keys if k.startswith("A_")]
B = [d["tile_range"][k] for k in keys if k.startswith("B_")]
bars = [("S2DS\n18", S2DS, g.PURPLE),
        ("MuS2\nA", float(np.mean(A)), g.BLUE),
        ("MuS2\nB", float(np.mean(B)), g.RED)]
xb = np.arange(len(bars))
ax2.bar(xb, [b[1] for b in bars], width=0.6, color=[b[2] for b in bars],
        edgecolor="white", linewidth=0.3, zorder=2)
for i, b in enumerate(bars):
    ax2.text(i, b[1] + 0.25, "%.2f" % b[1], ha="center", va="bottom",
             fontsize=6.0, color="#333333")
ax2.axhline(0.20, color="#888888", linestyle="--", linewidth=g.LW, zorder=1)
ax2.text(1.0, 14.6, "dashed: typical method gap 0.05-0.20 dB", fontsize=5.4,
         color="#666666", ha="center", va="top")
ax2.set_xticks(xb)
ax2.set_xticklabels([b[0] for b in bars], fontsize=6.0)
ax2.set_ylabel("PSNR range across sites (dB)")
ax2.set_ylim(0, 15.2)
ax2.set_xlim(-0.6, 2.6)
g.style(ax2)
g.panel_tag(ax2, "(b)", y=1.025)

g.save(fig, "fig4_mus2")
print("[grsl fig4 mus2 vertical] (b) S2DS=%.2f  A=%.2f  B=%.2f  figsize=%.1fx%.1f"
      % (S2DS, float(np.mean(A)), float(np.mean(B)), g.SINGLE, 5.0))
