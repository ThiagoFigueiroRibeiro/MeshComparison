"""Steps shared by both pipelines: load, normalize scale, measure the pre-alignment error and align with ICP."""
import os
from dataclasses import dataclass

import numpy as np

from .alignment import similarity_icp_align
from .distances import symmetric_mse
from .io import load_mesh


@dataclass
class PreparedMeshes:
    gt: object  # trimesh, scaled so the GT bounding-box diagonal is 1
    rm_aligned: object  # trimesh, same scale, aligned to the GT when the MSE threshold was exceeded
    internal_scale: float
    gt_diag_raw: float  # GT bounding-box diagonal in the input units
    pre_mse_norm: float
    alignment_triggered: bool
    final_transform: np.ndarray


def prepare_meshes(gt_path, rm_path, mse_threshold_normalized, total_steps):
    """Run steps ``[1..4/total_steps]`` of a pipeline (the step markers drive the GUI progress bar)."""
    print(f"[1/{total_steps}] Loading meshes...")
    gt = load_mesh(gt_path)
    rm = load_mesh(rm_path)

    print(f"[2/{total_steps}] Internal scale normalization...")
    gt_diag_raw = np.linalg.norm(gt.bounds[1] - gt.bounds[0])
    if gt_diag_raw < 1e-12:
        raise ValueError("GT mesh bounding-box diagonal is too small.")

    internal_scale = 1.0 / gt_diag_raw
    gt.apply_scale(internal_scale)
    rm.apply_scale(internal_scale)

    print(f"[3/{total_steps}] Computing pre-alignment MSE...")
    pre_mse_norm = symmetric_mse(gt.vertices, rm.vertices)
    alignment_triggered = pre_mse_norm > mse_threshold_normalized

    print(f"    Pre-alignment symmetric MSE (normalized): {pre_mse_norm:.8e}")
    print(f"    Threshold (normalized): {mse_threshold_normalized:.8e}")
    print(f"    Alignment triggered: {alignment_triggered}")

    rm_aligned = rm.copy()
    final_transform = np.eye(4)

    if alignment_triggered:
        print(f"[4/{total_steps}] Running similarity ICP alignment (RM -> GT)...")
        transform, fitness, inlier_rmse = similarity_icp_align(rm.vertices, gt.vertices)
        rm_aligned.apply_transform(transform)
        final_transform = transform
        print(f"    ICP fitness: {fitness:.6f}")
        print(f"    ICP inlier RMSE: {inlier_rmse:.6f}")
    else:
        print(f"[4/{total_steps}] Alignment skipped.")

    return PreparedMeshes(gt, rm_aligned, internal_scale, gt_diag_raw, pre_mse_norm,
                          alignment_triggered, final_transform)


def export_aligned(prepared, aligned_dir):
    """Write the aligned RM back in the input scale of the GT and return the file path."""
    export = prepared.rm_aligned.copy()
    export.apply_scale(1.0 / prepared.internal_scale)
    path = os.path.join(aligned_dir, "rm_aligned.ply")
    export.export(path)
    return path


def transform_columns(transform):
    """The 3 x 4 upper block of a 4 x 4 transform as ``final_transform_RC`` CSV columns."""
    return {f"final_transform_{r}{c}": transform[r, c] for r in range(3) for c in range(4)}
