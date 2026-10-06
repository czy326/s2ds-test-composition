"""生成 Table 1：18 site × 3 架构（3 种子 mean ± sd）的 valid PSNR 表。

数据源：E:\\论文4\\evidence\\aoi_matrix.json
输出：draft/table1.md（Markdown）与 draft/table1.csv
"""
import csv
import io
import json
import sys

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

P = r"E:\论文4\evidence\aoi_matrix.json"
OUT_MD = r"E:\论文4\draft\table1.md"
OUT_CSV = r"E:\论文4\draft\table1.csv"

d = json.load(open(P, encoding="utf-8"))
M = np.array(d["matrix_valid"], dtype=float)
combos = d["combos"]
aois = d["aois"]
split = d["aoi_split"]
MODELS = [("armD", "Mamba-MISR"), ("highresnet_cld", "HighRes-Net-cld"),
          ("breizhsr", "BreizhSR")]
SEEDS = ["2026", "2027", "2028"]

# 每个架构：18 维 mean 与 sd（跨 3 种子）
per_model = {}
for tag, _ in MODELS:
    rows = [[i for i, c in enumerate(combos) if c == "%s_s%s" % (tag, s)][0]
            for s in SEEDS]
    sub = M[rows, :]
    per_model[tag] = (np.nanmean(sub, axis=0), np.nanstd(sub, axis=0, ddof=1))

overall = np.nanmean(np.vstack([per_model[t][0] for t, _ in MODELS]), axis=0)
order = np.argsort(-overall)

lines = []
lines.append("**Table 1.** Valid PSNR (dB) at each of the 18 S2DS sites, per architecture "
             "(mean and standard deviation over three seeds). Sites are ordered by the "
             "mean of the three architectures. The last column is that mean. The bottom "
             "block summarises the dispersion.")
lines.append("")
hdr = "| Site | Split | " + " | ".join(n for _, n in MODELS) + " | Mean |"
lines.append(hdr)
lines.append("|---|---|" + "---|" * (len(MODELS) + 1))

csv_rows = [["site", "split"] + [n for _, n in MODELS] + ["mean"]]
for i in order:
    cells = []
    for tag, _ in MODELS:
        m, s = per_model[tag][0][i], per_model[tag][1][i]
        cells.append("%.2f ± %.2f" % (m, s))
    lines.append("| `%s` | %s | %s | %.2f |"
                 % (aois[i], split[aois[i]], " | ".join(cells), overall[i]))
    csv_rows.append([aois[i], split[aois[i]]]
                    + ["%.4f" % per_model[t][0][i] for t, _ in MODELS]
                    + ["%.4f" % overall[i]])

lines.append("")
lines.append("| Dispersion across the 18 sites | | " +
             " | ".join("%.2f" % (per_model[t][0].max() - per_model[t][0].min())
                        for t, _ in MODELS) + " | %.2f |" % (overall.max() - overall.min()))
lines.append("| Standard deviation across sites | | " +
             " | ".join("%.2f" % np.nanstd(per_model[t][0], ddof=1)
                        for t, _ in MODELS) + " | %.2f |" % np.nanstd(overall, ddof=1))

# 分区对照
for sp in ("train", "val", "test"):
    idx = [i for i, a in enumerate(aois) if split[a] == sp]
    lines.append("| %s partition mean (%d sites) | %d | " % (sp.capitalize(), len(idx), len(idx)) +
                 " | ".join("%.2f" % np.nanmean(per_model[t][0][idx]) for t, _ in MODELS) +
                 " | %.2f |" % np.nanmean(overall[idx]))

with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    csv.writer(f).writerows(csv_rows)

print("sites ordered (high -> low):")
for i in order:
    print("  %-20s %-6s " % (aois[i], split[aois[i]])
          + "  ".join("%7.3f" % per_model[t][0][i] for t, _ in MODELS)
          + "   mean %7.3f" % overall[i])
print()
print("range: " + "  ".join("%s=%.3f" % (n, per_model[t][0].max() - per_model[t][0].min())
                            for t, n in MODELS) + "  mean=%.3f" % (overall.max() - overall.min()))
print("std:   " + "  ".join("%s=%.3f" % (n, np.nanstd(per_model[t][0], ddof=1))
                            for t, n in MODELS) + "  mean=%.3f" % np.nanstd(overall, ddof=1))
for sp in ("train", "val", "test"):
    idx = [i for i, a in enumerate(aois) if split[a] == sp]
    print("%-6s n=%2d  " % (sp, len(idx))
          + "  ".join("%s=%.3f" % (n, np.nanmean(per_model[t][0][idx])) for t, n in MODELS))
print("\nwrote %s and %s" % (OUT_MD, OUT_CSV))
