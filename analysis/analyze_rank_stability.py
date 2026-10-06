r"""E1 + E5：排名稳定性统计检验 + 测试集规模曲线

数据源
──────
`E:\新方向研究\aoi_leak\aoi_matrix.json` —— 9 组合（3 架构 × 3 种子）× 18 AOI 的 valid PSNR 矩阵。

产物
────
`E:\论文4\evidence\rank_stability.json`

预注册判据（跑前写死，跑完按判据报，不改判）
──────────────────────────────────────────
  T1  armD vs HighRes-Net-cld 的 **AOI 配对差**（18 对，各用 3 种子平均）：
      Wilcoxon 符号秩检验 + rank-biserial 效应量 + bootstrap 95% CI。
      判据：p < 0.05 且 |rank-biserial| ≥ 0.50 ⇒ 两方法在 AOI 层面可区分；
            否则 ⇒ 在 AOI 层面不可区分（排名差异被地理构成掩盖）。
  T2  **精确翻转率**（穷举全部 C(18,k) 个子集，k=5）：
      落在 [0.20, 0.80] ⇒ 排名不可靠，主命题成立。
      ⚠ 用精确枚举而非 bootstrap —— 18 选 5 只有 8568 种，可以穷举。
  T3  方差分解 bootstrap 95% CI（重抽 AOI 与组合）：
      下界 > 1.0 ⇒ 地理构成主导。
  S1  (E5) k = 3…18 的翻转率曲线；报出使翻转率 ≤ 0.05 的最小 k。
  S2  统计单元声明：配对检验 n = 18（AOI），**不是** 1476（场景，那是伪重复）。

用法（WSL, conda emssm）
    python /mnt/e/论文4/evidence/analyze_rank_stability.py
"""
from __future__ import annotations

import io
import itertools
import json
import os
import sys

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

P = "/mnt/e/新方向研究/aoi_leak/aoi_matrix.json"
OUT = "/mnt/e/论文4/evidence/rank_stability.json"
NBOOT = 2000
MODELS = ["armD", "highresnet_cld", "breizhsr"]
SEEDS = ["2026", "2027", "2028"]
PAIR = ("armD", "highresnet_cld")

d = json.load(open(P, encoding="utf-8"))
M = np.array(d["matrix_valid"], dtype=float)        # (9, 18)
combos = d["combos"]
aois = d["aois"]
aoi_split = d["aoi_split"]

# 架构向量 = 3 种子平均
arch = {}
for m in MODELS:
    rows = [combos.index("%s_s%s" % (m, s)) for s in SEEDS]
    arch[m] = np.nanmean(M[rows, :], axis=0)

res = {
    "source": P,
    "n_aoi": len(aois),
    "aois": aois,
    "aoi_split": aoi_split,
    "arch_mean_unweighted": {m: float(np.mean(arch[m])) for m in MODELS},
}

# ---------------------------------------------------------------- T1 配对检验
a, b = arch[PAIR[0]], arch[PAIR[1]]
diff = b - a                                        # HN - armD
n = len(diff)
res["pair"] = list(PAIR)
res["pair_diff_mean"] = float(np.mean(diff))
res["pair_diff_median"] = float(np.median(diff))
res["T1_n_pairs"] = n

try:
    from scipy.stats import wilcoxon, rankdata
    st = wilcoxon(a, b)
    res["T1_wilcoxon_stat"] = float(st.statistic)
    res["T1_wilcoxon_p"] = float(st.pvalue)
    nz = diff[diff != 0]
    rk = rankdata(np.abs(nz))
    w_plus = float(rk[nz > 0].sum())
    w_minus = float(rk[nz < 0].sum())
    res["T1_rank_biserial"] = (w_plus - w_minus) / (w_plus + w_minus)
    res["T1_n_nonzero"] = int(len(nz))
    res["T1_verdict"] = bool(res["T1_wilcoxon_p"] < 0.05 and
                             abs(res["T1_rank_biserial"]) >= 0.50)
except Exception as e:                              # noqa: BLE001
    res["T1_error"] = str(e)

rng = np.random.default_rng(0)
bs = [float(np.mean(diff[rng.integers(0, n, n)])) for _ in range(NBOOT)]
res["T1_boot_ci95"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
res["T1_boot_contains_zero"] = bool(res["T1_boot_ci95"][0] <= 0 <= res["T1_boot_ci95"][1])

# ---------------------------------------------------------------- T2/S1 精确翻转率
def exact_flip(vec_a, vec_b, k):
    dd = vec_b - vec_a
    cnt = tot = 0
    for sel in itertools.combinations(dd, k):
        tot += 1
        if sum(sel) < 0:                            # b < a ⇒ a 赢
            cnt += 1
    return cnt / tot, tot


flip_curve = {}
for k in range(3, len(aois) + 1):
    fr, tot = exact_flip(arch[PAIR[0]], arch[PAIR[1]], k)
    flip_curve[k] = {"a_win_rate": fr, "n_subset": tot}

res["S1_flip_curve_%s_vs_%s" % PAIR] = {str(k): v for k, v in flip_curve.items()}
res["T2_flip_rate_k5"] = flip_curve[5]["a_win_rate"]
res["T2_n_subset_k5"] = flip_curve[5]["n_subset"]
res["T2_pass"] = bool(0.20 <= flip_curve[5]["a_win_rate"] <= 0.80)

small_k = [k for k in sorted(flip_curve) if flip_curve[k]["a_win_rate"] <= 0.05]
res["S1_min_k_for_5pct"] = int(min(small_k)) if small_k else None

# 三对架构的 k=5 翻转率（描述性）
pairwise = {}
for i in range(len(MODELS)):
    for j in range(i + 1, len(MODELS)):
        p, q = MODELS[i], MODELS[j]
        fr, tot = exact_flip(arch[p], arch[q], 5)
        pairwise["%s_vs_%s" % (p, q)] = {
            "p_win_rate": fr, "n_subset": tot,
            "mean_gap_dB": float(np.mean(arch[q]) - np.mean(arch[p])),
        }
res["pairwise_k5"] = pairwise

# ---------------------------------------------------------------- T3 方差分解 CI
aoi_mean = np.array([np.mean(M[:, i]) for i in range(len(aois))])
combo_mean = np.array([np.mean(M[c, :]) for c in range(M.shape[0])])
res["T3_var_aoi"] = float(np.var(aoi_mean, ddof=1))
res["T3_var_model"] = float(np.var(combo_mean, ddof=1))
res["T3_ratio"] = res["T3_var_aoi"] / res["T3_var_model"]

ratios = []
for _ in range(NBOOT):
    ai = rng.integers(0, M.shape[1], M.shape[1])
    ci = rng.integers(0, M.shape[0], M.shape[0])
    sub = M[np.ix_(ci, ai)]
    va = np.var(np.mean(sub, axis=0), ddof=1)
    vm = np.var(np.mean(sub, axis=1), ddof=1)
    if vm > 0:
        ratios.append(va / vm)
res["T3_ratio_ci95"] = [float(np.percentile(ratios, 2.5)),
                        float(np.percentile(ratios, 97.5))]
res["T3_pass"] = bool(res["T3_ratio_ci95"][0] > 1.0)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)

print("=== E1 + E5 判决 ===")
print("T1  %s vs %s : mean_diff=%+.4f dB  median=%+.4f  n=%d AOI"
      % (PAIR[0], PAIR[1], res["pair_diff_mean"], res["pair_diff_median"], n))
print("    wilcoxon p=%.4f  rank_biserial=%+.3f  boot CI95=[%+.4f, %+.4f]"
      % (res.get("T1_wilcoxon_p", float("nan")), res.get("T1_rank_biserial", float("nan")),
         res["T1_boot_ci95"][0], res["T1_boot_ci95"][1]))
print("    => T1 %s (可区分)" % ("PASS" if res.get("T1_verdict") else "FAIL(不可区分)"))
print("T2  精确翻转率 k=5 : %.4f  over %d subsets  => %s"
      % (res["T2_flip_rate_k5"], res["T2_n_subset_k5"],
         "PASS(排名不可靠)" if res["T2_pass"] else "FAIL"))
print("T3  var_aoi=%.4f var_model=%.4f ratio=%.2f CI95=[%.2f, %.2f] => %s"
      % (res["T3_var_aoi"], res["T3_var_model"], res["T3_ratio"],
         res["T3_ratio_ci95"][0], res["T3_ratio_ci95"][1],
         "PASS" if res["T3_pass"] else "FAIL"))
print("S1  最小 k（翻转率<=0.05）= %s" % res["S1_min_k_for_5pct"])
print("S1  flip curve:")
for k in sorted(flip_curve):
    print("      k=%2d  a_win=%.4f  (n=%d)" % (k, flip_curve[k]["a_win_rate"],
                                               flip_curve[k]["n_subset"]))
print("S1  pairwise k=5:")
for kk, vv in pairwise.items():
    print("      %-32s p_win=%.4f  gap=%+.4f dB" % (kk, vv["p_win_rate"], vv["mean_gap_dB"]))
print("DONE -> %s" % OUT)
