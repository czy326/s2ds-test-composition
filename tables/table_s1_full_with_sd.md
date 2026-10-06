**Table 1.** Valid PSNR (dB) at each of the 18 S2DS sites, per architecture (mean and standard deviation over three seeds). Sites are ordered by the mean of the three architectures. The last column is that mean. The bottom block summarises the dispersion.

| Site | Split | Mamba-MISR | HighRes-Net-cld | BreizhSR | Mean |
|---|---|---|---|---|---|
| `sjz_north_agri` | train | 29.83 ± 0.29 | 31.05 ± 0.06 | 28.93 ± 0.12 | 29.94 |
| `xian_plain` | train | 29.27 ± 0.12 | 30.48 ± 0.12 | 28.37 ± 0.16 | 29.37 |
| `chengdu_plain` | train | 31.09 ± 0.07 | 31.30 ± 0.06 | 25.64 ± 0.33 | 29.35 |
| `lanzhou_valley` | train | 29.16 ± 0.06 | 29.85 ± 0.04 | 28.94 ± 0.10 | 29.32 |
| `dunhuang_oasis` | test | 29.78 ± 0.81 | 28.12 ± 0.97 | 29.77 ± 0.30 | 29.23 |
| `linzhi_valley` | train | 28.91 ± 0.02 | 29.62 ± 0.02 | 28.41 ± 0.09 | 28.98 |
| `bj_south` | val | 27.84 ± 0.18 | 27.26 ± 0.09 | 27.36 ± 0.34 | 27.49 |
| `hohhot_steppe` | train | 26.15 ± 0.06 | 27.18 ± 0.05 | 26.55 ± 0.03 | 26.63 |
| `zhengzhou_east` | train | 26.13 ± 0.06 | 27.21 ± 0.09 | 26.15 ± 0.07 | 26.50 |
| `dg_north` | test | 27.01 ± 0.16 | 26.20 ± 0.12 | 24.61 ± 0.40 | 25.94 |
| `sz_east` | test | 26.33 ± 0.29 | 25.82 ± 0.03 | 25.24 ± 0.38 | 25.80 |
| `haikou_north` | test | 26.48 ± 0.41 | 25.72 ± 0.04 | 24.95 ± 0.59 | 25.72 |
| `kunming_plateau` | val | 25.72 ± 0.10 | 25.18 ± 0.10 | 24.74 ± 0.81 | 25.21 |
| `urumqi_north` | train | 24.68 ± 0.13 | 25.77 ± 0.08 | 24.84 ± 0.09 | 25.10 |
| `xiamen_inland` | test | 25.70 ± 0.11 | 24.69 ± 0.21 | 23.59 ± 0.21 | 24.66 |
| `wuhan_lake` | train | 24.15 ± 0.29 | 25.36 ± 0.32 | 23.76 ± 0.30 | 24.42 |
| `harbin_agri` | train | 23.51 ± 0.04 | 24.19 ± 0.01 | 23.49 ± 0.01 | 23.73 |
| `qingdao_inland` | val | 18.64 ± 0.22 | 18.23 ± 0.29 | 18.82 ± 0.11 | 18.56 |

| Dispersion across the 18 sites | | 12.45 | 13.08 | 10.96 | 11.38 |
| Standard deviation across sites | | 2.93 | 3.11 | 2.65 | 2.81 |
| Train partition mean (10 sites) | 10 | 27.29 | 28.20 | 26.51 | 27.33 |
| Val partition mean (3 sites) | 3 | 24.07 | 23.56 | 23.64 | 23.75 |
| Test partition mean (5 sites) | 5 | 27.06 | 26.11 | 25.63 | 26.27 |
