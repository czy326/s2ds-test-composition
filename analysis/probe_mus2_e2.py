"""E2 正式版：MuS2 上"地理构成主导"的外部复现（零训练，四基线）

设计（两条腿，互补）
────────────────────
设置 A（**自洽控制**，无任何配准/波段对应不确定性）
    GT   = HR(mul_band_k)
    输入 = HR 下采样 3× 后再上采样回原尺寸
    ⇒ 测的是「该 tile 的影像本身有多难重建」。三种插值：nearest / bilinear / bicubic。

设置 B（**真实跨传感器**，有配准不确定性，只作旁证）
    GT   = HR(mul_band_6)
    输入 = LR(b6) 上采样 3×（bicubic）。b6 是波段对应探查中与 mul_band_6 相关最高的。

掩膜：`final_masks_b4`（二值 0/255），统一用于两个波段。
⚠ 已知限制：波段对应未与官方协议核对；设置 B 只能作旁证，**若 A 与 B 结论不一致，以 A 为准**。

预注册判据（跑前写死，跑完按判据报，不改判）
──────────────────────────────────────────
  R0  覆盖：成功处理的场景数 >= 85（91 个中）。
  R1  极差：7 个 tile 的任一基线的 PSNR 极差 >= 5.0 dB ⇒ 复现成功。
  R2  同构：在「每 tile 取 1 场景」的 7 点子集上，4 个基线的排名在不同随机子集间
      发生翻转（任一方法对的胜率落在 [0.2, 0.8]）。
  R3  对照：报出 MuS2 的 tile 级极差与 S2DS 的 18-AOI 极差 11.38 dB 之比。

用法（WSL, conda emssm）
    python /mnt/e/论文4/evidence/probe_mus2_e2.py [N]   # N=每 tile 取几个场景，0/省略=全部
"""
from __future__ import annotations

import io
import itertools
import json
import os
import sys

import cv2
import numpy as np
import rasterio

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

IMG = "/home/czy/data/mus2/x/image_data"
MSK = "/home/czy/data/mus2/x/masks"
OUT = "/mnt/e/论文4/evidence/mus2_e2.json"
SCALE = 3
HR_BANDS = [3, 6]
LR_FOR_B = {3: "b3", 6: "b6"}
MASKDIR = "final_masks_b4"
INTERPS = {"nearest": cv2.INTER_NEAREST, "bilinear": cv2.INTER_LINEAR,
           "bicubic": cv2.INTER_CUBIC}
S2DS_RANGE = 11.375


def psnr(pred, gt, mask, peak=255.0):
    e = (pred - gt) ** 2
    m = e[mask]
    if m.size == 0:
        return float("nan")
    return 10.0 * np.log10(peak * peak / max(float(m.mean()), 1e-12))


def match_quantiles(src, ref, lo=0.01, hi=0.99, nb=99):
    """把 src 的分位数映射到 ref 的分位数。

    ⚠ 必须做这一步：LR 是 Sentinel-2 DN（0–65535），HR 是 uint8（0–255），
    两者辐射定标不同，直接相减会得到负 PSNR（实测 −8 ~ −20 dB）。
    """
    qs = np.linspace(lo, hi, nb)
    s = np.quantile(src, qs)
    r = np.quantile(ref, qs)
    s, idx = np.unique(s, return_index=True)
    r = r[idx]
    if s.size < 2:
        return src
    return np.interp(src, s, r)


def main():
    nper = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    scenes = sorted(os.listdir(IMG))
    by_tile = {}
    for s in scenes:
        by_tile.setdefault(s.split("_")[1], []).append(s)
    picks = []
    for t in sorted(by_tile):
        picks += by_tile[t] if not nper else by_tile[t][:nper]

    rows = []
    for i, s in enumerate(picks):
        B = os.path.join(IMG, s)
        mp = os.path.join(MSK, MASKDIR, "mask_%s.png" % s)
        if not os.path.exists(mp):
            continue
        mk = cv2.imread(mp, cv2.IMREAD_UNCHANGED)
        valid = mk == 255
        rec = {"tile": s.split("_")[1], "scene": s,
               "valid_frac": float(valid.mean())}
        for b in HR_BANDS:
            hp = os.path.join(B, "hr_resized", "mul_band_%d.tiff" % b)
            if not os.path.exists(hp):
                continue
            with rasterio.open(hp) as ds:
                hr = ds.read(1).astype(np.float32)
            H, W = hr.shape
            lr_sim = cv2.resize(hr, (W // SCALE, H // SCALE),
                                interpolation=cv2.INTER_AREA)
            for nm, code in INTERPS.items():
                up = cv2.resize(lr_sim, (W, H), interpolation=code)
                rec["A_%s_b%d" % (nm, b)] = psnr(up, hr, valid)
            lb = LR_FOR_B[b]
            ld = os.path.join(B, lb, "lrs")
            if os.path.isdir(ld):
                fs = sorted(os.listdir(ld))
                with rasterio.open(os.path.join(ld, fs[0])) as ds:
                    lr = ds.read(1).astype(np.float32)
                up = cv2.resize(lr, (W, H), interpolation=cv2.INTER_CUBIC)
                up = match_quantiles(up, hr)
                rec["B_bicubic_b%d" % b] = psnr(up, hr, valid)
        rows.append(rec)
        if (i + 1) % 10 == 0:
            print("  ...%d/%d" % (i + 1, len(picks)), flush=True)

    keys = sorted(k for k in rows[0] if k.startswith(("A_", "B_")))
    res = {"n_scene": len(rows), "keys": keys,
           "per_scene": rows, "tile_groups": {t: by_tile[t] for t in sorted(by_tile)}}

    # R0
    res["R0_n"] = len(rows)
    res["R0_pass"] = bool(len(rows) >= 85)
    # R1 / 逐 tile 均值
    tile_mean = {}
    for k in keys:
        v = {}
        for t in sorted(by_tile):
            vals = [r[k] for r in rows if r["tile"] == t and np.isfinite(r.get(k, np.nan))]
            if vals:
                v[t] = float(np.mean(vals))
        tile_mean[k] = v
    res["tile_mean"] = tile_mean
    rng = {k: (max(v.values()) - min(v.values())) for k, v in tile_mean.items() if len(v) >= 2}
    res["R1_range"] = rng
    res["R1_max_range"] = float(max(rng.values())) if rng else float("nan")
    res["R1_pass"] = bool(res["R1_max_range"] >= 5.0)
    res["R3_ratio_vs_s2ds"] = float(res["R1_max_range"] / S2DS_RANGE)

    # R2：7 点（每 tile 1 场景）子集上的排名翻转
    one = {}
    for t in sorted(by_tile):
        got = next((r for r in rows if r["tile"] == t), None)
        if got:
            one[t] = got
    tiles = sorted(one)
    if len(tiles) >= 4:
        flips = {}
        for a, b in itertools.combinations(keys, 2):
            cnt = tot = 0
            for k in range(4, len(tiles) + 1):
                for sub in itertools.combinations(tiles, k):
                    tot += 1
                    va = np.nanmean([one[t].get(a, np.nan) for t in sub])
                    vb = np.nanmean([one[t].get(b, np.nan) for t in sub])
                    if np.isfinite(va) and np.isfinite(vb) and va > vb:
                        cnt += 1
            flips["%s>%s" % (a, b)] = cnt / tot if tot else float("nan")
        res["R2_pair_winrates"] = flips
        res["R2_ambiguous"] = bool(any(0.2 <= v <= 0.8 for v in flips.values()
                                       if np.isfinite(v)))
        res["R2_pass"] = res["R2_ambiguous"]
    else:
        res["R2_pass"] = None

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

    print("\n=== E2 判决 ===")
    print("R0  n_scene=%d  %s" % (res["R0_n"], "PASS" if res["R0_pass"] else "FAIL"))
    for k in keys:
        v = tile_mean[k]
        print("  %-16s range=%.3f dB  tiles=%d" % (k, max(v.values()) - min(v.values()), len(v)))
    print("R1  最大极差=%.3f dB (>=5.0)  %s" % (res["R1_max_range"],
                                               "PASS" if res["R1_pass"] else "FAIL"))
    print("R3  与 S2DS(11.375 dB) 之比 = %.3f" % res["R3_ratio_vs_s2ds"])
    if res.get("R2_pair_winrates"):
        amb = [k for k, v in res["R2_pair_winrates"].items() if 0.2 <= v <= 0.8]
        print("R2  模糊对 %d 个  %s" % (len(amb), "PASS" if res["R2_pass"] else "FAIL"))
        for k, v in sorted(res["R2_pair_winrates"].items())[:6]:
            print("      %-28s %.3f" % (k, v))
    print("DONE -> %s" % OUT)


main()
