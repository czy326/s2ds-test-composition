r"""AOI 泄漏预检（零训练，复用论文3 的 armD checkpoint）

目的
────
量一个数：同一个 checkpoint 在「训练见过的 AOI」与「完全未见的测试 AOI」上的 PSNR 差。
这个差就是评测协议里空间泄漏（spatial leakage）的量级。

⚠ 口径说明（写作时必须保持）
  · train-split 评测 = 模型见过这些**精确样本**，因此它是泄漏量的**上界**。
  · 领域里常见的「随机 patch 划分」泄漏量介于 train-split 与 test-split 之间，
    因为训测来自同一 AOI 的不同 patch，不是同一个样本。
  · 本预检只给量级，不主张等价于任何具体方法的泄漏量。

预注册判据（跑前写死，跑完按判据报）
──────────────────────────────────
  L0  口径自检：test split 的 valid PSNR 与 canonical 27.2285（armD s2026，全 423 场景）
      相差 < 0.35 dB。超了说明本脚本口径与论文不一致，先查口径再谈结论。
  L1  泄漏量级：Δ_leak = PSNR(train) − PSNR(test)
        Δ ≥ 0.50 dB  ⇒ GO，方向成立
        Δ ≤ 0.20 dB  ⇒ DEAD，空间泄漏可忽略
        否则          ⇒ GRAY，需全量/多模型复核
  L2  逐 AOI 离散度（描述性，不设 PASS/FAIL）：18 个 AOI 的 valid PSNR 标准差。
      若 std 大于典型方法间差异（本领域常见 0.05–0.20 dB），
      则单一测试集上的方法排名不可靠。

用法（WSL, conda emssm）
    python /mnt/e/新方向研究/aoi_leak/probe_aoi_leak.py [NSUB]
    NSUB 省略或 0 = 全量
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

OUT = "/mnt/e/论文4/evidence/aoi_leak_precheck.json"
CANON_VALID_S2026 = 27.2285          # armD s2026, test split, 全 423 场景, valid
SPLITS = ("train", "val", "test")


def psnr_masked(pred, gt, mask, peak=1.0):
    """pred/gt: (C,H,W) in [0,1]; mask: (H,W) bool -> 通道广播后再取像素。"""
    err = (pred - gt) ** 2
    m = err[:, mask]
    if m.size == 0:
        return float("nan")
    mse = float(m.mean())
    return 10.0 * np.log10(peak * peak / max(mse, 1e-12))


def pick(n, nsub):
    if not nsub or nsub >= n:
        return list(range(n))
    step = n / float(nsub)
    return [int(i * step) for i in range(nsub)]


def main():
    nsub = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model, a, runname = load_armD(2026, dev)
    print("[precheck] %s dev=%s nsub=%s" % (runname, dev, nsub or "ALL"), flush=True)

    res = {"runname": runname, "nsub": nsub, "splits": {}}
    per_aoi = {}

    for split in SPLITS:
        ds = S2DS(split, shuffle=bool(a.get("shuffle_frames", False)),
                  seed=int(a.get("seed", 0)))
        idx = pick(len(ds), nsub)
        acc = {"valid": [], "hard": []}
        aoi_set = set()
        with torch.no_grad():
            for c, j in enumerate(idx):
                s = ds[j]
                out = model(lr=s["lr"][None].to(dev), q=s["q"][None].to(dev),
                            cld=s["cld"][None].to(dev),
                            dt=s["dt"][None].to(dev))[0].cpu().numpy()
                hr = s["hr"].numpy()
                valid, hard, _ = eval_masks(s)
                v = psnr_masked(out, hr, valid)
                h = psnr_masked(out, hr, hard)
                acc["valid"].append(v)
                acc["hard"].append(h)
                ao = str(s["aoi"])
                aoi_set.add(ao)
                per_aoi.setdefault(ao, {"split": split, "valid": [], "hard": []})
                per_aoi[ao]["valid"].append(v)
                per_aoi[ao]["hard"].append(h)
                if (c + 1) % 50 == 0:
                    print("   %s ...%d/%d" % (split, c + 1, len(idx)), flush=True)

        res["splits"][split] = {
            "n_total": len(ds),
            "n_eval": len(idx),
            "aois": sorted(aoi_set),
            "psnr_valid": float(np.nanmean(acc["valid"])),
            "psnr_hard": float(np.nanmean(acc["hard"])),
        }
        print("  [%s] n=%d valid=%.4f hard=%.4f"
              % (split, len(idx), res["splits"][split]["psnr_valid"],
                 res["splits"][split]["psnr_hard"]), flush=True)

    for k, v in per_aoi.items():
        v["psnr_valid"] = float(np.nanmean(v["valid"]))
        v["psnr_hard"] = float(np.nanmean(v["hard"]))
        v["n"] = len(v["valid"])
        del v["valid"], v["hard"]
    res["per_aoi"] = per_aoi

    dv = res["splits"]["train"]["psnr_valid"] - res["splits"]["test"]["psnr_valid"]
    dh = res["splits"]["train"]["psnr_hard"] - res["splits"]["test"]["psnr_hard"]
    vals = np.array([v["psnr_valid"] for v in per_aoi.values()])
    res["delta_leak_valid"] = dv
    res["delta_leak_hard"] = dh
    res["aoi_std_valid"] = float(np.nanstd(vals, ddof=1))
    res["aoi_range_valid"] = float(np.nanmax(vals) - np.nanmin(vals))
    res["L0_canon_diff"] = res["splits"]["test"]["psnr_valid"] - CANON_VALID_S2026
    res["L0_pass"] = bool(abs(res["L0_canon_diff"]) < 0.35)
    res["L1_verdict"] = "GO" if dv >= 0.50 else ("DEAD" if dv <= 0.20 else "GRAY")
    res["L2_note"] = "aoi_std=%.4f aoi_range=%.4f (n_aoi=%d)" % (
        res["aoi_std_valid"], res["aoi_range_valid"], len(per_aoi))

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("\n=== 判决 ===")
    print("L0 canon diff = %+.4f  %s" % (res["L0_canon_diff"],
                                         "PASS" if res["L0_pass"] else "FAIL"))
    print("L1 d_leak(valid) = %+.4f  d_leak(hard) = %+.4f  => %s" % (dv, dh, res["L1_verdict"]))
    print("L2 %s" % res["L2_note"])
    print("DONE")


main()
