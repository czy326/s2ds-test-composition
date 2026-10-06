# Supplementary Material

**Test-set geographic composition dominates method ranking in remote sensing
super-resolution evaluation**

This supplement carries the three items moved out of the five-page letter: the
per-site table with per-seed spread (Table S1), the scene-level figure (Fig. S1),
and the per-seed values behind every number quoted in Sections III-A to III-E.

---

## Table S1

Valid PSNR (dB) at each of the 18 S2DS sites, per architecture, as
mean $\pm$ standard deviation over three seeds. Sites are ordered by the mean of
the three architectures. `Tr` / `Va` / `Te` mark the training (10), validation (3)
and test (5) partitions.

| Site | Split | Mamba-MISR | HighRes-Net-cld | BreizhSR | Mean |
|---|---|---|---|---|---|
| sjz north agri | Tr | 29.83 ± 0.29 | 31.05 ± 0.06 | 28.93 ± 0.12 | 29.94 |
| xian plain | Tr | 29.27 ± 0.12 | 30.48 ± 0.12 | 28.37 ± 0.16 | 29.37 |
| chengdu plain | Tr | 31.09 ± 0.07 | 31.30 ± 0.06 | 25.64 ± 0.33 | 29.35 |
| lanzhou valley | Tr | 29.16 ± 0.06 | 29.85 ± 0.04 | 28.94 ± 0.10 | 29.32 |
| dunhuang oasis | Te | 29.78 ± 0.81 | 28.12 ± 0.97 | 29.77 ± 0.30 | 29.23 |
| linzhi valley | Tr | 28.91 ± 0.02 | 29.62 ± 0.02 | 28.41 ± 0.09 | 28.98 |
| bj south | Va | 27.84 ± 0.18 | 27.26 ± 0.09 | 27.36 ± 0.34 | 27.49 |
| hohhot steppe | Tr | 26.15 ± 0.06 | 27.18 ± 0.05 | 26.55 ± 0.03 | 26.63 |
| zhengzhou east | Tr | 26.13 ± 0.06 | 27.21 ± 0.09 | 26.15 ± 0.07 | 26.50 |
| dg north | Te | 27.01 ± 0.16 | 26.20 ± 0.12 | 24.61 ± 0.40 | 25.94 |
| sz east | Te | 26.33 ± 0.29 | 25.82 ± 0.03 | 25.24 ± 0.38 | 25.80 |
| haikou north | Te | 26.48 ± 0.41 | 25.72 ± 0.04 | 24.95 ± 0.59 | 25.72 |
| kunming plateau | Va | 25.72 ± 0.10 | 25.18 ± 0.10 | 24.74 ± 0.81 | 25.21 |
| urumqi north | Tr | 24.68 ± 0.13 | 25.77 ± 0.08 | 24.84 ± 0.09 | 25.10 |
| xiamen inland | Te | 25.70 ± 0.11 | 24.69 ± 0.21 | 23.59 ± 0.21 | 24.66 |
| wuhan lake | Tr | 24.15 ± 0.29 | 25.36 ± 0.32 | 23.76 ± 0.30 | 24.42 |
| harbin agri | Tr | 23.51 ± 0.04 | 24.19 ± 0.01 | 23.49 ± 0.01 | 23.73 |
| qingdao inland | Va | 18.64 ± 0.22 | 18.23 ± 0.29 | 18.82 ± 0.11 | 18.56 |
| **Range across sites** | | **12.45** | **13.08** | **10.96** | **11.38** |
| **Std across sites** | | 2.93 | 3.11 | 2.65 | 2.81 |
| **Train (10 sites) mean** | | 27.29 | 28.20 | 26.51 | 27.33 |
| **Val (3 sites) mean** | | 24.07 | 23.56 | 23.64 | 23.75 |
| **Test (5 sites) mean** | | 27.06 | 26.11 | 25.63 | 26.27 |

The last three rows are the source of the partition reversal discussed in
Section III-C of the paper: HighRes-Net-cld leads on the training partition,
Mamba-MISR leads on both the validation and the test partition, and
HighRes-Net-cld falls to last on the validation partition.

---

## Fig. S1

Not used. The scene-level figure appears in the paper as Fig. 3, in a single-column
vertical layout (two stacked panels) that fits the five-page limit without moving
it out. The vector file is `figures/grsl/fig3_scene_winrate.pdf`.

Numbers behind it: overall Mamba-MISR win rate 0.366, mean difference $-0.195$ dB,
quartile win rates 0.343, 0.366, 0.424, 0.331, correlation between scene difficulty
and the difference 0.17.

---

## Per-seed values

The nine model-seed combinations behind every number in Sections III-A to III-E.

| Combination | Mean over 18 sites | Std over 18 sites |
|---|---|---|
| armD s2026 | 26.7385 | 2.9296 |
| armD s2027 | 26.7166 | 3.0574 |
| armD s2028 | 26.6060 | 2.8973 |
| highresnet_cld s2026 | 26.8590 | 3.1013 |
| highresnet_cld s2027 | 26.8068 | 3.0695 |
| highresnet_cld s2028 | 26.8766 | 3.2058 |
| breizhsr s2026 | 25.7840 | 2.6879 |
| breizhsr s2027 | 25.7113 | 2.7720 |
| breizhsr s2028 | 25.8626 | 2.5883 |

---

## Data and code

- S2DS site-level matrix (9 combinations × 18 sites, plus per-scene PSNR):
  `evidence/aoi_matrix.json`
- Rank-stability statistics and exact enumeration: `evidence/rank_stability.json`
- Cross-partition leakage: `evidence/aoi_leak_precheck.json`
- Valid-pixel diagnostics: `evidence/qingdao_diag.json`, `evidence/qingdao_scenes.json`
- MuS2 replication: `evidence/mus2_e2.json`, `evidence/mus2_e2_analysis.json`
