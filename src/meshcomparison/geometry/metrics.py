import numpy as np

from ..common.distances import mse_from_errors, symmetric_vertex_errors


def compute_metrics(gt_vertices, rm_vertices):
    """
    Vertex-based symmetric metrics:
      - mean chamfer = average of mean NN distances in both directions
      - symmetric hausdorff = max NN distance in both directions
      - symmetric rmse = sqrt(average squared NN distance in both directions
    """
    d_gt2rm, d_rm2gt = symmetric_vertex_errors(gt_vertices, rm_vertices)

    chamfer_mean = 0.5 * (np.mean(d_gt2rm) + np.mean(d_rm2gt))
    hausdorff = max(np.max(d_gt2rm), np.max(d_rm2gt))
    rmse = np.sqrt(0.5 * (np.mean(d_gt2rm ** 2) + np.mean(d_rm2gt ** 2)))

    return {
        "d_gt2rm": d_gt2rm,
        "d_rm2gt": d_rm2gt,
        "mse": mse_from_errors(d_gt2rm, d_rm2gt),
        "chamfer_mean": chamfer_mean,
        "hausdorff": hausdorff,
        "rmse": rmse,
    }
