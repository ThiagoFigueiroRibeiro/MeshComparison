import numpy as np
from scipy.spatial import cKDTree


def maybe_subsample(points, max_points=50000, seed=0):
    if len(points) <= max_points:
        return points
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(points), size=max_points, replace=False)
    return points[idx]


def nn_distances(src_points, dst_points):
    tree = cKDTree(dst_points)
    dists, idx = tree.query(src_points, k=1, workers=-1)
    return dists, idx


def symmetric_vertex_errors(gt_vertices, rm_vertices):
    d_gt2rm, _ = nn_distances(gt_vertices, rm_vertices)
    d_rm2gt, _ = nn_distances(rm_vertices, gt_vertices)
    return d_gt2rm, d_rm2gt


def mse_from_errors(d_gt2rm, d_rm2gt):
    return 0.5 * (np.mean(d_gt2rm ** 2) + np.mean(d_rm2gt ** 2))


def symmetric_mse(gt_vertices, rm_vertices):
    d_gt2rm, d_rm2gt = symmetric_vertex_errors(gt_vertices, rm_vertices)
    return mse_from_errors(d_gt2rm, d_rm2gt)
