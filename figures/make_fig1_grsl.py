"""GRSL Fig. 1 — 逐 site 的 valid PSNR（**单栏宽**，按 3.5 in 出图）。

⚠ 关键：矢量 PDF 缩放会连带缩小字号，所以必须**按目标栏宽生成**。
本图按单栏 3.5 in 出图，site 标签用与 Table I 完全一致的站点 ID（下划线写成空格）。
"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

import figstyle_grsl as g

# 站点 ID 与 Table I 的 Site 列严格一致（下划线 -> 空格，控制标签宽度）
def label(a):
    return a.replace("_", " ")

M, combos, aois, aoi_split, d = g.load_matrix()
per_aoi = d["per_aoi_mean"]
vals = np.array([per_aoi[a] for a in aois], dtype=float)
order = np.argsort(vals)
ao_sorted = [aois[i] for i in order]
v_sorted = vals[order]

fig = plt.figure(figsize=(g.SINGLE, 4.4))
ax = fig.add_axes([0.315, 0.115, 0.655, 0.855])

y = np.arange(len(ao_sorted))
ax.barh(y, v_sorted, height=0.74,
        color=[g.SPLIT_COLORS[aoi_split[a]] for a in ao_sorted],
        edgecolor="white", linewidth=0.25, zorder=2)
for yy, vv in zip(y, v_sorted):
    ax.text(vv + 0.13, yy, "%.2f" % vv, va="center", ha="left", fontsize=5.4,
            color="#333333", zorder=3)

mu = float(v_sorted.mean())
ax.axvline(mu, color=g.GREY, linestyle="--", linewidth=g.LW, zorder=1)

top = len(ao_sorted) - 0.5
ax.set_yticks(y)
ax.set_yticklabels([label(a) for a in ao_sorted], fontsize=6.0)
ax.set_ylim(-3.1, top + 2.0)
ax.set_xlim(17.4, 31.6)
ax.set_xlabel("Valid PSNR (dB)")
ax.text(mu, top + 1.0, "mean %.2f dB" % mu, fontsize=6.0, color=g.GREY,
        ha="center", va="bottom", zorder=4,
        bbox=dict(facecolor="white", edgecolor="none", pad=0.9))

handles = [plt.Rectangle((0, 0), 1, 1, color=g.SPLIT_COLORS[s], ec="white", lw=0.25)
           for s in ("train", "val", "test")]
ax.legend(handles, ["train (10)", "val (3)", "test (5)"], loc="lower right",
          frameon=False, handlelength=0.9, borderpad=0.15, labelspacing=0.25,
          fontsize=5.6, bbox_to_anchor=(1.0, 0.12))

lo, hi = v_sorted.min(), v_sorted.max()
ax.annotate("", xy=(lo, -2.10), xytext=(hi, -2.10),
            arrowprops=dict(arrowstyle="<->", color="#555555", lw=g.LW))
ax.text((lo + hi) / 2 - 0.55, -2.35, "range %.2f dB" % (hi - lo), ha="center",
        va="top", fontsize=6.0, color="#333333", zorder=4,
        bbox=dict(facecolor="white", edgecolor="none", pad=0.9))

g.style(ax)
g.save(fig, "fig1_aoi_psnr")
print("[grsl fig1 single-col] n=%d range=%.3f std=%.3f mean=%.3f figsize=%.1fx4.4"
      % (len(ao_sorted), hi - lo, v_sorted.std(ddof=1), mu, g.SINGLE))
