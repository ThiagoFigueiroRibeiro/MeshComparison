# Mesh Comparison: Mesh Evaluation

This workspace compares a ground-truth mesh with a reconstructed mesh. Convert FBX models to STL (or another supported `trimesh` format) before running the evaluation scripts; they do not load FBX directly.

## Workspace layout

```text
MeshComparison/
├── gt.stl                         # Ground-truth mesh
├── mod.stl                        # Reconstructed/model mesh
├── mesh_eval_pipeline.py          # Geometric mesh comparison
├── percept_eval_pipeline.py       # Multi-view perceptual comparison
├── run_mesh_eval.bat              # Windows launcher for geometric evaluation
├── run_percept_eval.bat           # Windows launcher for perceptual evaluation
└── output/
    ├── aligned/                   # Aligned reconstructed mesh exports
    ├── heatmaps/                  # Geometric distance heatmap assets
    ├── metrics/                   # CSV metric reports
    └── renders/                   # Mesh and view renders
        ├── gt/
        ├── pairs/
        └── rm/
```

The launchers use `gt.stl` as the ground truth and `mod.stl` as the reconstructed mesh, and write results under `output/`. Runs may replace files with the same names in those output folders.

## Requirements

Use Python in a Conda environment named `meshEval` to run the supplied `.bat` files. The scripts import NumPy, pandas, trimesh, pyrender, Open3D, Matplotlib, imageio, and SciPy. The perceptual pipeline additionally imports scikit-image, PyTorch, and LPIPS. A working offscreen-rendering setup is needed for `pyrender`; the perceptual pipeline uses CUDA when available and otherwise runs LPIPS on CPU.

## Installation

```bash
conda create -n meshEval python=3.12
conda activate meshEval
pip install numpy pandas trimesh pyrender open3d matplotlib imageio scipy scikit-image torch lpips
```

For GPU-accelerated LPIPS, install the PyTorch build that matches your CUDA version using the official PyTorch installation instructions before installing the remaining packages.

## Run

From this folder in Windows, double-click either batch file or run it in a Command Prompt:

```bat
run_mesh_eval.bat
run_percept_eval.bat
```

To choose other input or output paths, call Python directly:

```bat
python mesh_eval_pipeline.py --gt gt.stl --rm mod.stl --out output
python percept_eval_pipeline.py --gt gt.stl --rm mod.stl --out output
```

Both scripts require `--gt` and `--rm`; `--out` defaults to `output`.

## Pipelines

### Geometric evaluation

`mesh_eval_pipeline.py` normalizes both meshes using the ground-truth bounding-box diagonal. It measures symmetric nearest-vertex distances, and runs similarity ICP (rotation, translation, and uniform scale) when the pre-alignment normalized MSE exceeds the configured threshold. It writes one shared-view render per mesh and a ground-truth vertex-distance heatmap.

Main outputs:

- `output/metrics/mesh_metrics.csv`: pre/post-alignment MSE, mean Chamfer distance, symmetric Hausdorff distance, symmetric RMSE, alignment status, and transform metadata. Distance metrics are reported both normalized and in the original ground-truth units.
- `output/aligned/rm_aligned.ply`: aligned reconstructed mesh, exported in the input ground-truth scale.
- `output/renders/gt_ortho.png` and `output/renders/rm_aligned_ortho.png`: orthographic renders.
- `output/heatmaps/gt_heatmap_ortho.png`: rendered distance heatmap; `gt_heatmap_colored.ply` is the colored mesh used to create it.

### Perceptual evaluation

`percept_eval_pipeline.py` uses the same normalization and conditional ICP alignment, then renders the meshes across a rotating set of camera azimuths. It computes masked LPIPS, PSNR, and SSIM per view and summarizes their distributions. By default, it evaluates 100 views and saves views 1, 33, and 66.

Main outputs:

- `output/metrics/per_view_metrics.csv`: one row per view with LPIPS, PSNR, SSIM, camera angle, and framing values.
- `output/metrics/metric_summary.csv`: min, max, 25th/75th percentiles, median, and mean for each perceptual metric.
- `output/metrics/run_metadata.csv`: input paths, alignment details, view settings, and the final transform.
- `output/aligned/rm_aligned.ply`: aligned reconstructed mesh in the ground-truth input scale.
- `output/renders/gt/`, `output/renders/rm/`, and `output/renders/pairs/`: saved images for the selected views.

## Options

Both scripts accept `--mse-threshold` (default `1e-4`), which controls whether alignment is run, plus `--width` and `--height` (defaults `1600` and `1200`). Use `--help` after the script name to see all options.

The geometric pipeline also accepts `--azimuth` (default `-135`) and `--elevation` (default `25.264`). The perceptual pipeline accepts `--elevation` (default `25.264`), `--num-views` (default `100`), `--save-views` (default `1 33 66`), `--camera-margin` (default `1.05`), and `--radius-factor` (default `1.45`).
