r"""AOI 矩阵：3 架构 × 3 种子 × 18 AOI 的 PSNR 矩阵 + 排名稳定性 bootstrap

背景（来自 probe_aoi_leak.py 全量预检）
────────────────────────────────────
同一 armD checkpoint 下：
  · Δ_leak(train − test) = +0.2355 dB (valid)  → 空间泄漏效应存在但极小，GRAY
  · 18 个 AOI 的 valid PSNR 极差 12.55 dB，std 2.98 dB
⇒ 原命题「泄漏导致虚高」不成立；改验更稳的命题。

命题
────
「测试集的地理构成决定方法排名」——若逐 AOI 离散度远大于方法间差异，
则任何单一测试集上的排名都不可靠。

预注册判据（跑前写死，跑完按判据报，不改判）
──────────────────────────────────────────
  J0  口径自检：armD s2026 在 test split（423 场景）全量的 valid PSNR
      必须 = 27.2285，diff < 1e-4。超了先查口径再谈结论。
  J1  排名稳定性：对 3 个架构（各 3 种子平均），做 1000 次「从 18 个 AOI
      随机抽 5 个」的 bootstrap，统计每个架构成为最优的频率。
      判据：若任一架构的「最优频率」落在 [0.20, 0.80] ⇒ 排名不可靠，命题成立。
  J2  方差分解：ratio = var(AOI 均值) / var(架构·种子 均值)。
      判据：ratio ≥ 10 ⇒ 地理构成主导，命题成立。
  J3  描述性（不设 PASS/FAIL）：18 AOI 的 valid PSNR 极差与 std。

用法（WSL, conda emssm）
    python /mnt/e/新方向研究/aoi_leak/probe_aoi_matrix.py [quick]
    quick = 只用 seed 2026（3 个组合），全量 = 9 个组合
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import torch

sys.path.insert(0, "/mnt/e/论文2")
sys.path.insert(0, "/mnt/e/论文2/dataset")
sys.path.insert(0, "/mnt/e/新方向研究/band_bound")

from probe_reliability_v2 import load_armD, eval_masks  # noqa: E402
from s2ds_dataset import S2DS                            # noqa: E402

OUT = "/mnt/e/论文4/evidence/aoi_matrix.json"
RUNS = "/mnt/e/论文2/runs_s2ds"
RUNMAP = {"highresnet_cld": "s2dsE9_highresnet_cld", "breizhsr": "s2dsE7_breizhsr"}
MODELS = ["armD", "highresnet_cld", "breizhsr"]
ALL_SEEDS = [2026, 2027, 2028]
SPLITS = ["train", "val", "test"]
CANON_TEST_VALID_S2026 = 27.2285
NBOOT, KTEST = 1000, 5


def psnr_masked(pred, gt, mask, peak=1.0):
    err = (pred - gt) ** 2
    m = err[:, mask]
    if m.size == 0:
        return float("nan")
    return 10.0 * np.log10(peak * peak / max(float(m.mean()), 1e-12))


def load_model(tag, seed, dev):
    if tag == "armD":
        return load_armD(seed, dev)
    from misr.build_any import build_from_spec
    rd = os.path.join(RUNS, "%s_s%d" % (RUNMAP[tag], seed))
    ck = torch.load(os.path.join(rd, "ckpt_030000.pt"), map_location="cpu",
                    weights_only=False)
    a = ck["args"]
    model = build_from_spec(a, cin=4, scale=4, c_default=32).to(dev)
    model.load_state_dict(ck["model"])
    model.eval()
    return model, a, "%s/ckpt_030000.pt" % os.path.basename(rd)


def main():
    seeds = [2026] if (len(sys.argv) > 1 and sys.argv[1] == "quick") else ALL_SEEDS
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    combos = [(t, s) for t in MODELS for s in seeds]
    print("[matrix] combos=%d dev=%s" % (len(combos), dev), flush=True)

    # 累积：acc[combo_index][aoi] = [psnr_sum, n]
    # 另存逐场景 PSNR（供逐样本胜率与按基线表现分层使用，见 figure skill 第 7 条）
    acc = {i: {} for i in range(len(combos))}
    aoi_split = {}
    scene_keys, scene_aoi = [], []
    scene_index = {}
    scene_psnr = {i: {} for i in range(len(combos))}

    meta = {}
    for split in SPLITS:
        ds_cache = {}
        for c, (tag, seed) in enumerate(combos):
            model, a, name = load_model(tag, seed, dev)
            # ⚠ 口径必须与论文一致：shuffle/seed 从 checkpoint 的 args 取。
            # 漏传会让 armD（shuffle_frames=True）的 PSNR 偏离 canonical 约 0.13 dB。
            sh = bool(a.get("shuffle_frames", False))
            sd = int(a.get("seed", 0))
            meta["%s_s%d" % (tag, seed)] = {"shuffle": sh, "seed": sd, "ckpt": name}
            key = (sh, sd)
            if key not in ds_cache:
                ds_cache[key] = S2DS(split, shuffle=sh, seed=sd)
                print("  [%s] ds(shuffle=%s,seed=%s) n=%d"
                      % (split, sh, sd, len(ds_cache[key])), flush=True)
            ds = ds_cache[key]
            done = 0
            with torch.no_grad():
                for j in range(len(ds)):
                    s = ds[j]
                    out = model(lr=s["lr"][None].to(dev), q=s["q"][None].to(dev),
                                cld=s["cld"][None].to(dev),
                                dt=s["dt"][None].to(dev))[0].cpu().numpy()
                    hr = s["hr"].numpy()
                    valid, _, _ = eval_masks(s)
                    ao = str(s["aoi"])
                    aoi_split[ao] = split
                    skey = "%s|%s" % (ao, str(s["scene"]))
                    if skey not in scene_index:
                        scene_index[skey] = len(scene_keys)
                        scene_keys.append(skey)
                        scene_aoi.append(ao)
                    v = psnr_masked(out, hr, valid)
                    if np.isfinite(v):
                        cell = acc[c].setdefault(ao, [0.0, 0])
                        cell[0] += v
                        cell[1] += 1
                        scene_psnr[c][skey] = v
                    done += 1
            print("    [%d/%d] %s s%d %s -> %d samples"
                  % (c + 1, len(combos), tag, seed, split, done), flush=True)
            del model
            if dev == "cuda":
                torch.cuda.empty_cache()
        del ds_cache

    aois = sorted(aoi_split)
    idx = {a: i for i, a in enumerate(aois)}

    # 矩阵
    M = np.full((len(combos), len(aois)), np.nan)
    for ci in range(len(combos)):
        for a, (ssum, nn) in acc[ci].items():
            if nn:
                M[ci, idx[a]] = ssum / nn

    combo_names = ["%s_s%d" % (t, s) for t, s in combos]
    res = {
        "combos": combo_names,
        "meta": meta,
        "aois": aois,
        "aoi_split": {a: aoi_split[a] for a in aois},
        "matrix_valid": M.tolist(),
        "per_combo": {nm: float(np.nanmean(M[ci]))
                      for ci, nm in enumerate(combo_names)},
        "per_aoi_mean": {a: float(np.nanmean(M[:, idx[a]])) for a in aois},
    }

    # 逐场景矩阵（行 = 组合，列 = scene_keys）
    SL = np.full((len(combos), len(scene_keys)), np.nan)
    for ci in range(len(combos)):
        for k, skey in enumerate(scene_keys):
            SL[ci, k] = scene_psnr[ci].get(skey, np.nan)
    res["scene_keys"] = scene_keys
    res["scene_aoi"] = scene_aoi
    res["matrix_scene"] = SL.tolist()

    # J0 —— 必须用**逐样本**口径（论文口径）校验；矩阵/分析用 AOI 未加权口径
    ci0 = combos.index(("armD", 2026))
    test_cols = [idx[a] for a in aois if aoi_split[a] == "test"]
    test_mean_uw = float(np.nanmean(M[ci0, test_cols]))
    ts = sum(acc[ci0][a][0] for a in aois if aoi_split[a] == "test")
    tn = sum(acc[ci0][a][1] for a in aois if aoi_split[a] == "test")
    test_mean_pw = ts / tn
    res["J0_test_valid_persample"] = test_mean_pw
    res["J0_test_valid_aoiunweighted"] = test_mean_uw
    res["J0_note"] = ("J0 用逐样本口径校验（论文口径）；矩阵与 J1/J2 用 AOI 未加权口径。"
                      "两者在 test split 上相差 %+.4f dB" % (test_mean_uw - test_mean_pw))
    res["J0_diff"] = test_mean_pw - CANON_TEST_VALID_S2026
    res["J0_pass"] = bool(abs(res["J0_diff"]) < 1e-4)

    # J3
    aoi_mean = np.array([res["per_aoi_mean"][a] for a in aois])
    res["J3_aoi_std"] = float(np.nanstd(aoi_mean, ddof=1))
    res["J3_aoi_range"] = float(np.nanmax(aoi_mean) - np.nanmin(aoi_mean))

    # J2 方差分解
    combo_mean = np.array([res["per_combo"][c] for c in res["combos"]])
    v_aoi = float(np.nanvar(aoi_mean, ddof=1))
    v_mod = float(np.nanvar(combo_mean, ddof=1))
    res["J2_var_aoi"] = v_aoi
    res["J2_var_model"] = v_mod
    res["J2_ratio"] = v_aoi / v_mod if v_mod > 0 else float("inf")
    res["J2_pass"] = bool(res["J2_ratio"] >= 10.0)

    # J1 排名 bootstrap（每架构用种子平均）
    arch_vec = {}
    for t in MODELS:
        rows = [combos.index((t, s)) for s in seeds if (t, s) in combos]
        arch_vec[t] = np.nanmean(M[rows, :], axis=0)
    rng = np.random.default_rng(0)
    best_ct = {t: 0 for t in MODELS}
    span = []
    for _ in range(NBOOT):
        sel = rng.choice(len(aois), KTEST, replace=False)
        m = {t: float(np.nanmean(arch_vec[t][sel])) for t in MODELS}
        best_ct[max(m, key=m.get)] += 1
        span.append(max(m.values()) - min(m.values()))
    res["J1_best_freq"] = {t: best_ct[t] / float(NBOOT) for t in MODELS}
    res["J1_mean_arch"] = {t: float(np.nanmean(arch_vec[t])) for t in MODELS}
    res["J1_span_mean"] = float(np.mean(span))
    res["J1_span_p95"] = float(np.percentile(span, 95))
    res["J1_ambiguous"] = bool(any(0.20 <= v <= 0.80
                                   for v in res["J1_best_freq"].values()))
    res["J1_pass"] = res["J1_ambiguous"]

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

    print("\n=== 判决 ===")
    print("J0 diff=%.2e %s" % (res["J0_diff"], "PASS" if res["J0_pass"] else "FAIL"))
    print("J2 var_aoi=%.4f var_model=%.4f ratio=%.1f %s"
          % (v_aoi, v_mod, res["J2_ratio"], "PASS" if res["J2_pass"] else "FAIL"))
    print("J1 best_freq=%s ambiguous=%s %s"
          % (res["J1_best_freq"], res["J1_ambiguous"], "PASS" if res["J1_pass"] else "FAIL"))
    print("J3 aoi_std=%.4f aoi_range=%.4f" % (res["J3_aoi_std"], res["J3_aoi_range"]))
    print("DONE")


main()
