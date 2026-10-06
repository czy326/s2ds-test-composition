# Test-Set Geographic Composition Dominates Method Ranking in Remote Sensing Super-Resolution Evaluation

Companion code and per-site results for the manuscript submitted to
*IEEE Geoscience and Remote Sensing Letters* (GRSL).

Authors: Zhengyang Chen, Dawei Liu (corresponding), Zhiheng Liu —
Engineering University of PAP, Xi'an 710000, China.

## What the paper does

Remote-sensing super-resolution is usually evaluated on a handful of
geographically distinct sites, and methods are ranked by gaps of one or two
tenths of a decibel. This paper asks how much of such a ranking is decided by
*which* sites happen to sit in the test set.

Three multi-temporal Sentinel-2 networks (Mamba-MISR, HighRes-Net-cld,
BreizhSR), three seeds each, are evaluated on all 18 sites of the S2DS
benchmark separately. Every possible *k*-site test subset is enumerated
exactly. The two strongest networks differ by 0.16 dB on average and are not
separable at the site level, while the same networks vary by 11.38 dB across
sites; drawing five sites at random moves the mean score by 6.54 dB. At least
16 sites are needed before a 0.16 dB gap becomes resolvable. The effect
reproduces on MuS2, an independently built public benchmark, where no model is
trained at all.

## Repository layout

| Path | Contents |
|---|---|
| `paper/` | LaTeX source, `IEEEtran.cls`, and the compiled PDF |
| `figures/` | Figures 1–5 (vector PDF + PNG) and the matplotlib scripts that draw them |
| `tables/` | Table I (per-site PSNR, seed means) and supplementary Table S1 (with per-seed spread) |
| `analysis/` | Probe/analysis scripts and their raw JSON and numeric outputs |

### Tables

- `tables/table1_per_site_psnr.csv` — Table I of the paper: valid PSNR (dB) at
  each of the 18 S2DS sites, mean over three seeds, for the three
  architectures. Columns: `site, split, M-MISR, HN-cld, Breizh, mean`.
- `tables/table_s1_full_with_sd.csv` — supplementary Table S1: same layout with
  the per-seed standard deviation reported alongside each mean.
- `tables/supplementary_grsl.md` — supplementary text describing Table S1 and
  the per-seed values.

### Analysis outputs

- `analysis/aoi_matrix.json` — the per-site × per-model-seed PSNR matrix that
  every other number in the paper is derived from
  (`matrix_valid`, `combos`, `aois`, `aoi_split`).
- `analysis/rank_stability.json` — exact enumeration of win rates over all
  *k*-site subsets.
- `analysis/mus2_e2.json`, `analysis/mus2_e2_analysis.json` — the MuS2
  replication (zero-training baselines, Settings A and B).
- `analysis/aoi_leak_precheck.json` — precheck confirming the split is by site
  and that no area appears in two partitions.

## Data

The S2DS benchmark used here is not publicly released, so this repository
contains code and results tables only, not imagery. It is built from real
Sentinel-2 Level-2A acquisitions (bands B02, B03, B04, B08; 12 frames per
sample at 40 m; a 10 m target for the reference date; scale factor 4), split by
site into 10 training, 3 validation and 5 test sites.

The external replication uses **MuS2**, which is public:
P. Kowaleczko *et al.*, "MuS2: A real-world benchmark for Sentinel-2
multi-image super-resolution," *Scientific Data*, vol. 10, 2023, Art. 712.

## Reproducing the figures

Each figure has a self-contained script that reads the JSON files in
`analysis/` and writes a vector PDF plus a PNG:

```bash
python figures/make_fig1_grsl.py   # per-site PSNR
python figures/make_fig2_grsl.py   # win rate vs number of test sites
python figures/make_fig3_grsl.py   # scene-level differences and quartiles
python figures/make_fig4_grsl.py   # MuS2 replication
python figures/make_fig5_grsl.py   # valid-pixel fraction vs PSNR
```

Shared styling lives in `figures/figstyle_grsl.py`.

## Compiling the paper

```bash
cd paper
pdflatex "Test-Set Geographic Composition Dominates Method Ranking in Remote Sensing Super-Resolution Evaluation.tex"
pdflatex "Test-Set Geographic Composition Dominates Method Ranking in Remote Sensing Super-Resolution Evaluation.tex"
```

Run it twice so that cross-references and figure numbers resolve. The document
uses only `amsmath`, `amssymb`, `graphicx`, `booktabs`, `multirow`, `url` and
`hyperref`.

## Note on figure numbering

The scripts are named after the figure they produce in the submitted
manuscript. `make_fig4_grsl.py` produces Figure 4 (MuS2) and
`make_fig5_grsl.py` produces Figure 5 (valid-pixel fraction); older file names
in the working tree use the opposite order and should be ignored.
