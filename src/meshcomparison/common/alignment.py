import numpy as np

from .distances import maybe_subsample


def to_o3d_pcd(points):
    import open3d as o3d

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points.astype(np.float64))
    return pcd


def initial_similarity_from_bboxes(src_pts, tgt_pts):
    src_center = src_pts.mean(axis=0)
    tgt_center = tgt_pts.mean(axis=0)

    src_diag = np.linalg.norm(src_pts.max(axis=0) - src_pts.min(axis=0)) + 1e-12
    tgt_diag = np.linalg.norm(tgt_pts.max(axis=0) - tgt_pts.min(axis=0)) + 1e-12
    s = tgt_diag / src_diag

    T = np.eye(4, dtype=np.float64)
    T[:3, :3] = np.eye(3) * s
    T[:3, 3] = tgt_center - s * src_center
    return T


def similarity_icp_align(rm_vertices, gt_vertices,
                         coarse_dist=0.25,
                         fine_dist=0.05,
                         max_points=50000,
                         max_iter=100):
    """
    Similarity ICP: rotation + translation + uniform scale.
    """
    import open3d as o3d

    rm_pts = maybe_subsample(rm_vertices, max_points=max_points, seed=1)
    gt_pts = maybe_subsample(gt_vertices, max_points=max_points, seed=2)

    src = to_o3d_pcd(rm_pts)
    tgt = to_o3d_pcd(gt_pts)

    init_T = initial_similarity_from_bboxes(rm_pts, gt_pts)
    est = o3d.pipelines.registration.TransformationEstimationPointToPoint(with_scaling=True)

    coarse = o3d.pipelines.registration.registration_icp(
        src, tgt, coarse_dist, init_T, est,
        o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=max_iter)
    )

    fine = o3d.pipelines.registration.registration_icp(
        src, tgt, fine_dist, coarse.transformation, est,
        o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=max_iter)
    )

    return fine.transformation, fine.fitness, fine.inlier_rmse
