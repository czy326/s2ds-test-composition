import json
import numpy as np

P = r"E:\新方向研究\aoi_leak\aoi_leak_precheck.json"
OUT = r"E:\新方向研究\aoi_leak\aoi_span.txt"

d = json.load(open(P, encoding="utf-8"))
per = d["per_aoi"]
aois = sorted(per)
v = np.array([per[a]["psnr_valid"] for a in aois])

lines = []
lines.append("n_aoi=%d" % len(aois))
lines.append("aoi-level: mean=%.4f std=%.4f range=%.4f min=%.4f max=%.4f"
             % (v.mean(), v.std(ddof=1), v.max() - v.min(), v.min(), v.max()))

rng = np.random.default_rng(0)
for k in (5, 10, 18):
    means = []
    for _ in range(4000):
        sel = rng.choice(len(aois), k, replace=False)
        means.append(v[sel].mean())
    m = np.array(means)
    lines.append("subset k=%2d: mean=%.4f std=%.4f min=%.4f max=%.4f span=%.4f p5=%.4f p95=%.4f"
                 % (k, m.mean(), m.std(ddof=1), m.min(), m.max(),
                    m.max() - m.min(), np.percentile(m, 5), np.percentile(m, 95)))

lines.append("")
lines.append("per-AOI sorted (valid PSNR):")
for a in sorted(aois, key=lambda x: -per[x]["psnr_valid"]):
    lines.append("  %-20s %-6s %8.4f  n=%d" % (a, per[a]["split"], per[a]["psnr_valid"], per[a]["n"]))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("done")
