"""GRSL Fig. 5 — valid 像素占比 vs PSNR（单栏宽 3.5 in）。

⚠ 图号由 tex 中的插入顺序决定（按正文首次引用顺序编号）：
valid 占比在 §III-F 首次引用，晚于 §III-E 的 MuS2 复现 ⇒ 本图是 **Fig. 5**。
输出文件名用 fig5_*，与图号保持一致。

数据：evidence/qingdao_diag.json 的 per_aoi
输出：figures/grsl/fig5_validfrac.{png,pdf}
"""
from __future__ import annotations

import json

import numpy as np
import matplotlib.pyplot as plt

import figstyle_grsl as g

d = json.load(open(g.EV / "qingdao_diag.json", encoding="utf-8"))
per = d["per_aoi"]
aois = sorted(per, key=lambda a: per[a]["valid_mean"])
vf = np.array([per[a]["valid_mean"] for a in aois])
ps = np.array([per[a]["psnr_valid"] for a in aois])
sp = [per[a]["split"] for a in aois]

r = float(np.corrcoef(vf, ps)[0, 1])
k, b = np.polyfit(vf, ps, 1)

fig = plt.figure(figsize=(g.SINGLE, 2.75))
ax = fig.add_axes([0.185, 0.175, 0.785, 0.75])

xs = np.linspace(-0.02, 1.04, 50)
ax.plot(xs, k * xs + b, color=g.GREY, linestyle="--", linewidth=g.LW, zorder=1)
for s in ("train", "val", "test"):
    m = np.array([x == s for x in sp])
    ax.scatter(vf[m], ps[m], s=16, color=g.SPLIT_COLORS[s], edgecolors="white",
               linewidths=0.4, zorder=3, label="%s (%d)" % (s, int(m.sum())))

# 站点名与 Table I 一致（下划线 -> 空格）；两个标注分别放右侧/左侧空白处，避免压住散点
for a, dx, dy, ha in (("qingdao_inland", 0.020, -0.45, "left"),
                      ("wuhan_lake", -0.020, 0.55, "right")):
    i = aois.index(a)
    ax.annotate(a.replace("_", " "), xy=(vf[i], ps[i]),
                xytext=(vf[i] + dx, ps[i] + dy), fontsize=6.0, color="#444444",
                ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", color="#999999", lw=g.LW,
                                shrinkA=0, shrinkB=2))

ax.set_xlabel("Valid (cloud-free) pixel fraction")
ax.set_ylabel("Valid PSNR (dB)")
ax.set_xlim(-0.03, 1.06)
ax.set_ylim(16.6, 31.6)
ax.text(0.975, 0.955, "$r$ = %.2f" % r, transform=ax.transAxes, fontsize=6.4,
        color="#555555", ha="right", va="top")
ax.legend(loc="lower right", frameon=False, handletextpad=0.3, borderpad=0.15,
          labelspacing=0.25, fontsize=6.0)

g.style(ax)
g.save(fig, "fig5_validfrac")
print("[grsl fig5 validfrac] r=%.4f  valid range %.4f-%.4f"
      % (r, vf.min(), vf.max()))
