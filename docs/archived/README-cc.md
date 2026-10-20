<p align="center">
  <img src="../assets/mesh-comparison-logo.svg" width="180" alt="Mesh Comparison logo">
</p>

> **Archived documentation:** this snapshot describes the legacy script-based version. Its installation commands, file layout, and CLI options no longer describe the current package. Use the [current project README](../../README.md) and [documentation index](../README.md) for current instructions.

<h1 align="center">Mesh Comparison</h1>

<p align="center">
  <a href="https://github.com/lianeheidemann/mesh-comparison/actions/workflows/ci.yml">
    <img
      src="https://img.shields.io/github/actions/workflow/status/lianeheidemann/mesh-comparison/ci.yml?branch=main&style=flat-square&logo=githubactions&logoColor=white&label=CI%20%2F%20Build&labelColor=315f7d"
      alt="CI Build Status"
    />
  </a>
  <img src="https://img.shields.io/badge/license-proprietary%20fork-lightgrey?style=flat-square" alt="License: proprietary fork">
</p>

<p align="center">
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/Python-3B4A5A?style=flat-square&logo=python&logoColor=white"><img src="https://img.shields.io/badge/Python-61778E?style=flat-square&logo=python&logoColor=white" alt="Python"></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/NumPy-3B4A5A?style=flat-square&logo=numpy&logoColor=white"><img src="https://img.shields.io/badge/NumPy-61778E?style=flat-square&logo=numpy&logoColor=white" alt="NumPy"></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/Trimesh-3B4A5A?style=flat-square"><img src="https://img.shields.io/badge/Trimesh-61778E?style=flat-square" alt="Trimesh"></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/Open3D-3B4A5A?style=flat-square"><img src="https://img.shields.io/badge/Open3D-61778E?style=flat-square" alt="Open3D"></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/PyTorch-3B4A5A?style=flat-square&logo=pytorch&logoColor=white"><img src="https://img.shields.io/badge/PyTorch-61778E?style=flat-square&logo=pytorch&logoColor=white" alt="PyTorch"></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/LPIPS-3B4A5A?style=flat-square"><img src="https://img.shields.io/badge/LPIPS-61778E?style=flat-square" alt="LPIPS"></picture>
</p>

Mesh Comparison measures how close a **reconstructed 3D mesh** is to a **ground-truth mesh**. It aligns the two models, then produces two complementary reports:

- **Geometric** — distances between the surfaces (Chamfer, Hausdorff, RMSE) plus a deviation heatmap.
- **Perceptual** — how similar the meshes *look* across many camera angles (LPIPS, PSNR, SSIM).

> The documentation in [`docs/`](../README.md) is written in Portuguese. This README is in English.

## Contents

- [Quick start](#quick-start)
- [Input meshes](#input-meshes)
- [Metrics at a glance](#metrics-at-a-glance)
- [Pipelines and outputs](#pipelines-and-outputs)
- [Example results](#example-results)
- [Options](#options)
- [Documentation](#documentation)
- [Installation details and technologies](#installation-details-and-technologies)
- [Project layout](#project-layout)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License and credits](#license-and-credits)

## Quick start

```bat
conda env create -f environment.yml
conda activate meshEval
run_mesh_eval.bat
run_percept_eval.bat
```

The launchers compare `gt.stl` (ground truth) with `mod.stl` (reconstruction) and write everything under `output/`. Re-running replaces files with the same names.

On Linux or macOS, call the scripts directly (see [Options](#options) for custom paths):

```bash
python mesh_eval_pipeline.py --gt gt.stl --rm mod.stl --out output
python percept_eval_pipeline.py --gt gt.stl --rm mod.stl --out output
```

## Input meshes

Both scripts load meshes with `trimesh`. They **do not read FBX directly**: convert FBX models to STL (or another format supported by `trimesh`, such as PLY or OBJ) first. `--gt` and `--rm` are required.

## Metrics at a glance

| Metric | Pipeline | What it measures | Better |
| --- | --- | --- | --- |
| Chamfer (mean) | Geometric | Average nearest-vertex distance between the two meshes, in both directions. | Lower |
| Hausdorff (symmetric) | Geometric | Worst-case nearest-vertex distance; sensitive to outliers. | Lower |
| RMSE (symmetric) | Geometric | Root-mean-square nearest-vertex distance. | Lower |
| LPIPS | Perceptual | Learned perceptual distance between rendered views. | Lower |
| PSNR | Perceptual | Pixel-level fidelity between rendered views, in dB. | Higher |
| SSIM | Perceptual | Structural similarity of rendered views (0–1). | Higher |

Geometric distances are reported both **normalized** (by the ground-truth bounding-box diagonal) and in the **original ground-truth units**. For a plain-language explanation of each metric and its limits, see [Understanding mesh evaluation](../avaliacao-geometrica/README.md).

## Pipelines and outputs

### Geometric evaluation — `mesh_eval_pipeline.py`

Normalizes both meshes by the ground-truth bounding-box diagonal and measures symmetric nearest-vertex distances. If the pre-alignment normalized MSE exceeds the threshold, it runs similarity ICP (rotation, translation, uniform scale). It then renders one shared view per mesh and a ground-truth vertex-distance heatmap.

| Output | Content |
| --- | --- |
| `output/metrics/metrics_geometry.csv` | Pre/post-alignment MSE, Chamfer, Hausdorff, RMSE, alignment status and transform. |
| `output/aligned/rm_aligned.ply` | Aligned reconstructed mesh, in the input ground-truth scale. |
| `output/renders/gt_ortho.png`, `rm_aligned_ortho.png` | Orthographic renders. |
| `output/heatmaps/gt_heatmap_ortho.png` | Rendered distance heatmap (`gt_heatmap_colored.ply` is the colored mesh behind it). |

### Perceptual evaluation — `percept_eval_pipeline.py`

Uses the same normalization and conditional ICP, then renders both meshes from a rotating set of camera azimuths (100 views by default; views 1, 33 and 66 are saved). It computes masked LPIPS, PSNR and SSIM per view and summarizes their distributions.

| Output | Content |
| --- | --- |
| `output/metrics/per_view_metrics.csv` | One row per view: LPIPS, PSNR, SSIM, camera angle, framing. |
| `output/metrics/metrics_perceptual.csv` | Min, max, 25th/75th percentile, median and mean per metric. |
| `output/metrics/run_metadata.csv` | Input paths, alignment details, view settings, final transform. |
| `output/aligned/rm_aligned.ply` | Aligned reconstructed mesh. |
| `output/renders/gt/`, `rm/`, `pairs/` | Saved images for the selected views. |

## Example results

Sample values from the bundled `gt.stl` / `mod.stl` run (alignment was not triggered):

| Metric | Value |
| --- | --- |
| Mean Chamfer (normalized) | 0.00187 |
| Symmetric Hausdorff (normalized) | 0.0816 |
| Symmetric RMSE (normalized) | 0.00854 |
| LPIPS (median over 100 views) | 0.113 |
| PSNR (median over 100 views) | 11.13 dB |
| SSIM (median over 100 views) | 0.931 |

<table>
  <tr>
    <td width="50%" align="center">
      <strong>Ground-truth mesh (GT)</strong><br>
      <img src="../../examples/output/renders/gt_ortho.png" width="100%" alt="Orthographic render of the ground-truth mesh">
    </td>
    <td width="50%" align="center">
      <strong>Aligned reconstructed mesh (RM)</strong><br>
      <img src="../../examples/output/renders/rm_aligned_ortho.png" width="100%" alt="Orthographic render of the aligned reconstructed mesh">
    </td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <strong>Geometric distance heatmap</strong><br>
      <img src="../../examples/output/heatmaps/gt_heatmap_ortho.png" width="70%" alt="Geometric distance heatmap on the ground-truth mesh">
    </td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <strong>Perceptual comparison — view 1</strong><br>
      <img src="../../examples/output/renders/pairs/pair_view001.png" width="100%" alt="Side-by-side perceptual comparison of GT and RM for view 1">
    </td>
  </tr>
</table>

More metrics and views are in the [full example report](../results/README.md).

## Options

| Option | Pipeline | Default | Description |
| --- | --- | --- | --- |
| `--gt`, `--rm` | both | required | Ground-truth and reconstructed mesh paths. |
| `--out` | both | `output` | Output folder. |
| `--mse-threshold` | both | `1e-4` | Normalized MSE above which ICP alignment runs. |
| `--width`, `--height` | both | `1600`, `1200` | Render size in pixels. |
| `--azimuth` | geometric | `-135` | Camera azimuth (degrees). |
| `--elevation` | both | `25.264` | Camera elevation (degrees). |
| `--num-views` | perceptual | `100` | Number of rendered views. |
| `--save-views` | perceptual | `1 33 66` | Views whose images are saved. |
| `--camera-margin` | perceptual | `1.05` | Framing margin. |
| `--radius-factor` | perceptual | `1.45` | Camera distance factor. |

Run `python <script> --help` for the full list.

## Documentation

All documentation is in Portuguese; read the conceptual guide before the tutorial.

- [Documentation index](../README.md)
- [Understanding mesh evaluation](../avaliacao-geometrica/README.md) — criteria, geometric and perceptual metrics, limitations.
- [Implementation tutorial](../implementation/README.md) — step-by-step guide to building the pipelines.
- [Current results](../results/README.md) — recorded metrics and visualizations.

## Installation details and technologies

`environment.yml` creates the `meshEval` Conda environment (Python 3.12) with unpinned pip dependencies, which may resolve to different versions over time. To recreate the recorded Windows environment with exact versions, use the snapshot:

```bat
conda env create -f environment-lock.yml
```

If `meshEval` already exists, activate it instead. Verify the imports before running the pipelines:

```bat
python -c "import numpy, pandas, trimesh, pyrender, open3d, matplotlib, imageio, scipy, skimage, torch, torchvision, lpips; print('OK: libraries loaded')"
```

The validated environment used CPU-only PyTorch. For GPU-accelerated LPIPS, install a PyTorch build matching your CUDA version from the official PyTorch instructions. See the [environment preparation guide](../implementation/step-by-step/01-preparacao-ambiente.md) for validation details.

<details>
<summary>Technologies</summary>

| Technology | Role in the project |
| --- | --- |
| Python, Conda | Language and isolated environment. |
| NumPy, pandas | Numerical operations; tabular metrics and CSV exports. |
| Trimesh | Loading, inspecting, transforming and exporting meshes. |
| Open3D | ICP mesh alignment. |
| SciPy (cKDTree) | Nearest-neighbor searches for geometric metrics. |
| pyrender, imageio | Offscreen rendering and writing images. |
| Matplotlib | Distance visualization and heatmap color mapping. |
| PyTorch, torchvision, LPIPS | Learned perceptual similarity (CUDA optional). |
| scikit-image | SSIM calculation. |

Exact versions are recorded in [`environment-lock.yml`](../../environments/environment-lock.yml).

</details>

## Project layout

```text
mesh-comparison/
├── gt.stl                      # Ground-truth mesh
├── mod.stl                     # Reconstructed mesh
├── mesh_eval_pipeline.py       # Geometric comparison
├── percept_eval_pipeline.py    # Multi-view perceptual comparison
├── run_mesh_eval.bat           # Windows launcher (geometric)
├── run_percept_eval.bat        # Windows launcher (perceptual)
├── environment.yml             # General (unpinned) environment
├── environment-lock.yml        # Recorded Windows environment
├── ruff.toml                   # Lint configuration
├── tests/                      # pytest suite
├── docs/                       # Concepts, tutorial and results (Portuguese)
├── ../assets/                     # Logos and diagrams
├── .github/workflows/ci.yml    # Continuous integration
└── output/
    ├── aligned/                # Aligned reconstructed mesh
    ├── heatmaps/               # Distance heatmap assets
    ├── metrics/                # CSV reports
    └── renders/                # gt/, rm/ and pairs/ images
```

## Development

From the activated environment:

```bash
ruff check .
pytest
```

GitHub Actions ([`ci.yml`](../../.github/workflows/ci.yml)) runs lint, the tests and `--help` for both scripts. It does not run the rendering or CUDA parts of the pipelines.

## Troubleshooting

- **`pyrender` fails to create an offscreen context** — a working offscreen OpenGL setup is required. On headless Linux, install `libegl1 libgl1 libglu1-mesa libosmesa6` and set `PYOPENGL_PLATFORM=egl` (as the CI does).
- **CUDA not available** — expected on CPU-only installs; LPIPS then runs on CPU, just slower.
- **Cannot load an `.fbx` file** — convert it to STL/PLY/OBJ first (see [Input meshes](#input-meshes)).

## License and credits

This repository is a fork of [ThiagoFigueiroRibeiro/MeshComparison](https://github.com/ThiagoFigueiroRibeiro/MeshComparison). The modifications in this fork are proprietary; see [LICENSE](../../LICENSE). Code derived from the original project remains the property of its author.
