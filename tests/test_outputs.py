import numpy as np
import pandas as pd
import trimesh

from meshcomparison.gui.outputs import heatmap_range, load_run_meshes


def _write_run(out):
    (out / "aligned").mkdir(parents=True)
    (out / "heatmaps").mkdir()
    (out / "metrics").mkdir()
    sphere = trimesh.creation.icosphere()
    shifted = sphere.copy()
    shifted.apply_translation([0.05, 0.0, 0.0])
    shifted.export(out / "aligned" / "rm_aligned.ply")
    sphere.export(out / "heatmaps" / "gt_heatmap_colored.ply")
    pd.DataFrame([{"gt_bbox_diagonal_original_units": 3.5}]).to_csv(
        out / "metrics" / "metrics_geometry.csv", index=False)
    return sphere, shifted


def test_run_meshes_read_scale_and_recompute_legend_range(tmp_path):
    gt = tmp_path / "gt.ply"
    sphere, shifted = _write_run(tmp_path / "out")
    sphere.export(gt)

    meshes = load_run_meshes(str(gt), str(tmp_path / "out"), with_heatmap=True)

    assert meshes.rm_aligned is not None and meshes.heatmap is not None
    assert meshes.heatmap_scale == 3.5
    assert 0 < meshes.heatmap_vmax <= 0.05 + 1e-6  # nearest-vertex distances of a 0.05 shift are at most 0.05


def test_run_meshes_without_geometric_pipeline_has_no_heatmap(tmp_path):
    gt = tmp_path / "gt.ply"
    sphere, _ = _write_run(tmp_path / "out")
    sphere.export(gt)

    meshes = load_run_meshes(str(gt), str(tmp_path / "out"), with_heatmap=False)
    assert meshes.heatmap is None and meshes.heatmap_vmax is None


def test_heatmap_range_is_the_95th_percentile_of_gt_to_rm_distances():
    gt = trimesh.creation.icosphere(subdivisions=2)
    rm = gt.copy()
    rm.vertices = rm.vertices * 1.1  # radial offset of 0.1 for every vertex
    assert np.isclose(heatmap_range(gt, rm), 0.1, atol=2e-2)
