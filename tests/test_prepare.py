from pathlib import Path

import numpy as np
import trimesh

from meshcomparison.common.prepare import export_aligned, prepare_meshes, transform_columns

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples"


def test_prepare_skips_icp_when_the_threshold_is_not_exceeded(capsys):
    prepared = prepare_meshes(str(SAMPLES / "gt.stl"), str(SAMPLES / "gt.stl"), 1e-4, 7)
    assert not prepared.alignment_triggered
    assert np.allclose(prepared.final_transform, np.eye(4))
    assert prepared.pre_mse_norm == 0.0
    assert "[4/7] Alignment skipped." in capsys.readouterr().out


def test_prepare_aligns_and_exports_in_the_input_scale(tmp_path, capsys):
    moved = trimesh.load(SAMPLES / "gt.stl")
    moved.apply_transform(trimesh.transformations.rotation_matrix(0.3, [0, 0, 1]))
    moved.apply_translation([0.4 * moved.scale, 0, 0])
    moved_path = tmp_path / "moved.stl"
    moved.export(moved_path)

    prepared = prepare_meshes(str(SAMPLES / "gt.stl"), str(moved_path), 1e-4, 8)
    assert prepared.alignment_triggered
    assert abs(np.linalg.norm(prepared.gt.bounds[1] - prepared.gt.bounds[0]) - 1.0) < 1e-9
    assert "[4/8] Running similarity ICP" in capsys.readouterr().out

    path = Path(export_aligned(prepared, str(tmp_path)))
    assert path.name == "rm_aligned.ply" and path.is_file()


def test_transform_columns_are_row_major():
    columns = transform_columns(np.arange(16, dtype=float).reshape(4, 4))
    assert list(columns)[:5] == [f"final_transform_{n}" for n in ("00", "01", "02", "03", "10")]
    assert len(columns) == 12 and columns["final_transform_23"] == 11.0
