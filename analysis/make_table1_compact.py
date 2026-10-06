"""生成 GRSL 版紧凑 Table 1：只报三架构的种子均值，去掉 ±sd，一行一 site。

数据源：E:\\论文4\\evidence\\aoi_matrix.json
输出：draft/table1_compact.md（正文用）与 draft/table1_compact.csv
完整体（带 ±sd）仍由 make_table1.py 产出，作补充材料 Table S1。
"""
import csv
import io
import json
import sys

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

P = r"E:\论文4\evidence\aoi_matrix.json"
OUT_MD = r"E:\论文4\draft\table1_compact.md"
OUT_CSV = r"E:\论文4\draft\table1_compact.csv"

d = json.load(open(P, encoding="utf-8"))
M = np.array(d["matrix_valid"], dtype=float)
combos, aois, split = d["combos"], d["aois"], d["aoi_split"]
MODELS = [("armD", "M-MISR"), ("highresnet_cld", "HN-cld"), ("breizhsr", "Breizh")]
SEEDS = ["2026", "2027", "2028"]

pm = {}
for tag, _ in MODELS:
    rows = [[i for i, c in enumerate(combos) if c == "%s_s%s" % (tag, s)][0]
            for s in SEEDS]
    pm[tag] = np.nanmean(M[rows, :], axis=0)

overall = np.nanmean(np.vstack([pm[t] for t, _ in MODELS]), axis=0)
order = np.argsort(-overall)

L = []
L.append("TABLE I")
L.append("Valid PSNR (dB) at each S2DS site (mean over three seeds)")
L.append("")
L.append("| Site | Split | " + " | ".join(n for _, n in MODELS) + " | Mean |")
L.append("|---|---|" + "---|" * (len(MODELS) + 1))
SPLAB = {"train": "Tr", "val": "Va", "test": "Te"}
for i in order:
    L.append("| %s | %s | " % (aois[i].replace("_", " "), SPLAB[split[aois[i]]])
             + " | ".join("%.2f" % pm[t][i] for t, _ in MODELS)
             + " | %.2f |" % overall[i])
L.append("| **Range** | | " + " | ".join("**%.2f**" % (pm[t].max() - pm[t].min())
                                          for t, _ in MODELS)
         + " | **%.2f** |" % (overall.max() - overall.min()))
L.append("| **Std** | | " + " | ".join("%.2f" % np.nanstd(pm[t], ddof=1)
                                        for t, _ in MODELS)
         + " | %.2f |" % np.nanstd(overall, ddof=1))
for sp, lab in (("train", "Train (10)"), ("val", "Val (3)"), ("test", "Test (5)")):
    idx = [i for i, a in enumerate(aois) if split[a] == sp]
    L.append("| **%s mean** | | " % lab
             + " | ".join("%.2f" % np.nanmean(pm[t][idx]) for t, _ in MODELS)
             + " | %.2f |" % np.nanmean(overall[idx]))

with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["site", "split"] + [n for _, n in MODELS] + ["mean"])
    for i in order:
        w.writerow([aois[i], split[aois[i]]] + ["%.4f" % pm[t][i] for t, _ in MODELS]
                   + ["%.4f" % overall[i]])

print("rows=%d cols=%d" % (len(order) + 3, len(MODELS) + 3))
print("range: " + " ".join("%s=%.2f" % (n, pm[t].max() - pm[t].min())
                           for t, n in MODELS) + " mean=%.2f" % (overall.max() - overall.min()))
print("wrote %s" % OUT_MD)
