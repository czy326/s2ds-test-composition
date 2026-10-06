"""论文4 GRSL 版图样式：在 figstyle 基础上改尺寸、字号与输出目录。

IEEE GRSL 图件规格
──────────────────
  · 单栏宽 3.5 in (88 mm)，双栏宽 7.16 in (182 mm)
  · 图中文字 >= 8 pt，彩色图 >= 300 dpi
  · 交付 PDF（矢量）+ PNG（300 dpi）；PNG 仅作预览，投稿用 PDF
所有 GRSL 图脚本 import 本模块，不要再直接改 figstyle.py。
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import rcParams

import figstyle as fs

# 输出到 figures/grsl/，不覆盖带审阅标注的旧图
FIG = fs.FIG / "grsl"
FIG.mkdir(parents=True, exist_ok=True)
EV = fs.EV

rcParams.update({
    "font.size": 8.0,
    "axes.labelsize": 8.0,
    "axes.titlesize": 8.0,
    "xtick.labelsize": 7.2,
    "ytick.labelsize": 7.2,
    "legend.fontsize": 6.8,
    "axes.linewidth": 0.55,
    "xtick.major.width": 0.55,
    "ytick.major.width": 0.55,
    "savefig.dpi": 600,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

LW = 0.55
SINGLE = 3.5          # 单栏宽 (in)
DOUBLE = 7.16         # 双栏宽 (in)

# 复用 figstyle 的命名与颜色
BLUE, RED, GREEN = fs.BLUE, fs.RED, fs.GREEN
ORANGE, PURPLE, GREY = fs.ORANGE, fs.PURPLE, fs.GREY
TAGS, NAMES, COLORS, SEEDS = fs.TAGS, fs.NAMES, fs.COLORS, fs.SEEDS
SPLIT_COLORS = fs.SPLIT_COLORS

style = fs.style
panel_tag = fs.panel_tag
panel_cap = fs.panel_cap
show = fs.show
audit_text = fs.audit_text
gs = fs.gs
load_matrix = fs.load_matrix
arch_vectors = fs.arch_vectors


def save(fig, name, do_audit=True):
    """GRSL 版 save：600 dpi PNG（预览）+ 矢量 PDF；输出到 figures/grsl/。"""
    ok = audit_text(fig, name) if do_audit else True
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=600, bbox_inches="tight",
                    facecolor="white")
    import matplotlib.pyplot as plt
    plt.close(fig)
    print("saved grsl/%s%s" % (name, "" if ok else "   <-- 有重叠，需修"), flush=True)
    return ok
