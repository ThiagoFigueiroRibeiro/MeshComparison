import os
import argparse
import numpy as np
import pandas as pd
import trimesh
import pyrender
import open3d as o3d
import matplotlib.pyplot as plt
import matplotlib as mpl
import imageio.v2 as imageio

from scipy.spatial import cKDTree


# ============================================================
# Utilities
# ============================================================

def ensure_dirs(base_out):
    paths = {
        "renders": os.path.join(base_out, "renders"),
        "heatmaps": os.path.join(base_out, "heatmaps"),
        "metrics": os.path.join(base_out, "metrics"),
        "aligned": os.path.join(base_out, "aligned"),
    }
    for p in paths.values():
        os.makedirs(p, exist_ok=True)
    return paths


def apply_transform_points(points, T):
    pts_h = np.hstack([points, np.ones((len(points), 1), dtype=np.float64)])
    out = (T @ pts_h.T).T
    return out[:, :3]


def bounds_corners(bounds):
    mn, mx = bounds
    return np.array([
        [mn[0], mn[1], mn[2]],
        [mn[0], mn[1], mx[2]],
        [mn[0], mx[1], mn[2]],
        [mn[0], mx[1], mx[2]],
        [mx[0], mn[1], mn[2]],
        [mx[0], mn[1], mx[2]],
        [mx[0], mx[1], mn[2]],
        [mx[0], mx[1], mx[2]],
    ], dtype=np.float64)


def look_at(eye, target, up=np.array([0.0, 0.0, 1.0])):
    eye = np.asarray(eye, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    up = np.asarray(up, dtype=np.float64)

    forward = target - eye
    forward /= np.linalg.norm(forward) + 1e-12

    right = np.cross(forward, up)
    if np.linalg.norm(right) < 1e-8:
        up = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        right = np.cross(forward, up)

    right /= np.linalg.norm(right) + 1e-12
    true_up = np.cross(right, forward)
    true_up /= np.linalg.norm(true_up) + 1e-12

    pose = np.eye(4, dtype=np.float64)
    pose[:3, 0] = right
    pose[:3, 1] = true_up
    pose[:3, 2] = -forward
    pose[:3, 3] = eye
    return pose


def maybe_subsample(points, max_points=50000, seed=0):
    if len(points) <= max_points:
        return points
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(points), size=max_points, replace=False)
    return points[idx]


def to_o3d_pcd(points):
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points.astype(np.float64))
    return pcd


def nn_distances(src_points, dst_points):
    tree = cKDTree(dst_points)
    dists, idx = tree.query(src_points, k=1)
    return dists, idx


# ============================================================
# Mesh Loader (STL / OBJ / PLY / etc.)
# ============================================================

def load_mesh(path):
    """
    Loads STL/OBJ/PLY/etc. using trimesh.
    This does NOT support FBX.
    """
    ext = os.path.splitext(path)[1].lower()

    if ext == ".fbx":
        raise ValueError(
            f"FBX is not supported in this STL pipeline: {path}\n"
            f"Please convert FBX -> STL first and pass .stl files."
        )

    try:
        loaded = trimesh.load(path, force='scene', process=False, maintain_order=True)

        if isinstance(loaded, trimesh.Trimesh):
            mesh = loaded.copy()

        elif isinstance(loaded, trimesh.Scene):
            # bake transforms from the scene graph
            meshes = []
            for name, geom in loaded.geometry.items():
                # apply scene transform for each geometry instance
                for node_name in loaded.graph.nodes_geometry:
                    # graph.get returns transform from node to world
                    try:
                        transform, geom_name = loaded.graph[node_name]
                    except Exception:
                        continue
                    if geom_name != name:
                        continue
                    g = geom.copy()
                    g.apply_transform(transform)
                    meshes.append(g)

            if len(meshes) == 0:
                # fallback: concatenate geometries without transforms
                geoms = [g.copy() for g in loaded.geometry.values()]
                if len(geoms) == 0:
                    raise ValueError(f"No geometry found in: {path}")
                mesh = geoms[0] if len(geoms) == 1 else trimesh.util.concatenate(geoms)
            else:
                mesh = meshes[0] if len(meshes) == 1 else trimesh.util.concatenate(meshes)

        else:
            raise TypeError(f"Unsupported loaded type for {path}: {type(loaded)}")

        mesh.remove_unreferenced_vertices()
        return mesh

    except Exception as e:
        raise RuntimeError(f"Could not load mesh file: {path}\nReason: {e}")


# ============================================================
# Metrics
# ============================================================

def symmetric_vertex_errors(gt_vertices, rm_vertices):
    d_gt2rm, _ = nn_distances(gt_vertices, rm_vertices)
    d_rm2gt, _ = nn_distances(rm_vertices, gt_vertices)
    return d_gt2rm, d_rm2gt


def symmetric_mse(gt_vertices, rm_vertices):
    d_gt2rm, d_rm2gt = symmetric_vertex_errors(gt_vertices, rm_vertices)
    mse = 0.5 * (np.mean(d_gt2rm ** 2) + np.mean(d_rm2gt ** 2))
    return mse


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
        "chamfer_mean": chamfer_mean,
        "hausdorff": hausdorff,
        "rmse": rmse,
    }


# ============================================================
# Registration
# ============================================================

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


# ============================================================
# Rendering
# ============================================================

def build_shared_camera(meshes, azimuth_deg=45.0, elevation_deg=35.264, margin=1.15):
    all_vertices = np.vstack([m.vertices for m in meshes])
    mn = all_vertices.min(axis=0)
    mx = all_vertices.max(axis=0)
    center = 0.5 * (mn + mx)
    extents = mx - mn
    diag = np.linalg.norm(extents) + 1e-12

    az = np.deg2rad(azimuth_deg)
    el = np.deg2rad(elevation_deg)
    radius = 2.5 * diag

    eye = center + radius * np.array([
        np.cos(el) * np.cos(az),
        np.cos(el) * np.sin(az),
        np.sin(el)
    ])

    cam_pose = look_at(eye, center, up=np.array([0.0, 0.0, 1.0]))

    corners = bounds_corners(np.array([mn, mx]))
    view = np.linalg.inv(cam_pose)
    corners_cam = apply_transform_points(corners, view)

    xmag = np.max(np.abs(corners_cam[:, 0])) * margin
    ymag = np.max(np.abs(corners_cam[:, 1])) * margin
    zfar = max(10.0 * diag, 10.0)

    return {
        "pose": cam_pose,
        "xmag": float(xmag),
        "ymag": float(ymag),
        "zfar": float(zfar)
    }


def add_default_lights(scene):
    light = pyrender.DirectionalLight(color=np.ones(3), intensity=3.0)

    poses = []
    poses.append(np.eye(4))

    p2 = np.eye(4)
    p2[:3, 3] = [2, 2, 2]
    poses.append(p2)

    p3 = np.eye(4)
    p3[:3, 3] = [-2, -2, 2]
    poses.append(p3)

    for p in poses:
        scene.add(light, pose=p)


def render_mesh(mesh, out_path, camera_cfg,
                width=1600, height=1200,
                bg_color=(255, 255, 255, 255),
                smooth=True):
    scene = pyrender.Scene(
        bg_color=np.array(bg_color) / 255.0,
        ambient_light=np.array([0.35, 0.35, 0.35, 1.0])
    )

    render_mesh = pyrender.Mesh.from_trimesh(mesh, smooth=smooth)
    scene.add(render_mesh)

    cam = pyrender.OrthographicCamera(
        xmag=camera_cfg["xmag"],
        ymag=camera_cfg["ymag"],
        znear=0.01,
        zfar=camera_cfg["zfar"]
    )
    scene.add(cam, pose=camera_cfg["pose"])
    add_default_lights(scene)

    renderer = pyrender.OffscreenRenderer(viewport_width=width, viewport_height=height)
    color, _ = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
    renderer.delete()

    imageio.imwrite(out_path, color)
    return color


# ============================================================
# Heatmap
# ============================================================

def colorize_gt_heatmap(gt_mesh, d_gt2rm, cmap_name="RdYlGn_r", robust_percentile=95):
    heat_mesh = gt_mesh.copy()

    vmax = np.nanpercentile(d_gt2rm, robust_percentile)
    vmax = max(vmax, 1e-12)

    norm = mpl.colors.Normalize(vmin=0.0, vmax=vmax)
    cmap = plt.get_cmap(cmap_name)

    colors = (cmap(norm(d_gt2rm)) * 255).astype(np.uint8)
    heat_mesh.visual.vertex_colors = colors

    return heat_mesh, norm, cmap


def save_heatmap_figure(rendered_rgba, out_path, norm, cmap, label="Distance GT→RM"):
    fig = plt.figure(figsize=(12, 9), dpi=150)
    ax = fig.add_axes([0.03, 0.03, 0.82, 0.94])
    ax.imshow(rendered_rgba)
    ax.axis("off")

    cax = fig.add_axes([0.88, 0.12, 0.03, 0.76])
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cax)
    cbar.set_label(label)

    fig.savefig(out_path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


# ============================================================
# Main Pipeline
# ============================================================

def run_pipeline(gt_path, rm_path, out_dir,
                 mse_threshold_normalized=1e-4,
                 azimuth_deg=45.0,
                 elevation_deg=35.264,
                 width=1600,
                 height=1200):
    paths = ensure_dirs(out_dir)

    print("[1/7] Loading meshes...")
    gt_raw = load_mesh(gt_path)
    rm_raw = load_mesh(rm_path)

    print("[2/7] Internal scale normalization...")
    gt = gt_raw.copy()
    rm = rm_raw.copy()

    gt_diag_raw = np.linalg.norm(gt.bounds[1] - gt.bounds[0])
    if gt_diag_raw < 1e-12:
        raise ValueError("GT mesh bounding-box diagonal is too small.")

    internal_scale = 1.0 / gt_diag_raw
    gt.apply_scale(internal_scale)
    rm.apply_scale(internal_scale)

    print("[3/7] Computing pre-alignment MSE...")
    pre_mse_norm = symmetric_mse(gt.vertices, rm.vertices)
    alignment_triggered = pre_mse_norm > mse_threshold_normalized

    print(f"    Pre-alignment symmetric MSE (normalized): {pre_mse_norm:.8e}")
    print(f"    Threshold (normalized): {mse_threshold_normalized:.8e}")
    print(f"    Alignment triggered: {alignment_triggered}")

    rm_aligned = rm.copy()
    final_transform = np.eye(4)

    if alignment_triggered:
        print("[4/7] Running similarity ICP alignment (RM -> GT)...")
        T, fitness, inlier_rmse = similarity_icp_align(
            rm.vertices,
            gt.vertices
        )
        rm_aligned.apply_transform(T)
        final_transform = T
        print(f"    ICP fitness: {fitness:.6f}")
        print(f"    ICP inlier RMSE: {inlier_rmse:.6f}")
    else:
        print("[4/7] Alignment skipped.")

    print("[5/7] Computing final metrics...")
    post_mse_norm = symmetric_mse(gt.vertices, rm_aligned.vertices)
    metrics = compute_metrics(gt.vertices, rm_aligned.vertices)

    chamfer_gt_units = metrics["chamfer_mean"] * gt_diag_raw
    hausdorff_gt_units = metrics["hausdorff"] * gt_diag_raw
    rmse_gt_units = metrics["rmse"] * gt_diag_raw

    pre_mse_gt_units_sq = pre_mse_norm * (gt_diag_raw ** 2)
    post_mse_gt_units_sq = post_mse_norm * (gt_diag_raw ** 2)

    print("[6/7] Rendering orthographic views and heatmap...")
    cam_cfg = build_shared_camera(
        [gt, rm_aligned],
        azimuth_deg=azimuth_deg,
        elevation_deg=elevation_deg
    )

    gt_render_path = os.path.join(paths["renders"], "gt_ortho.png")
    rm_render_path = os.path.join(paths["renders"], "rm_aligned_ortho.png")

    render_mesh(gt, gt_render_path, cam_cfg, width=width, height=height)
    render_mesh(rm_aligned, rm_render_path, cam_cfg, width=width, height=height)

    heat_mesh, norm, cmap = colorize_gt_heatmap(gt, metrics["d_gt2rm"])
    heat_mesh_path = os.path.join(paths["heatmaps"], "gt_heatmap_colored.ply")
    heat_img_tmp = os.path.join(paths["heatmaps"], "_gt_heatmap_render_tmp.png")
    heat_img_final = os.path.join(paths["heatmaps"], "gt_heatmap_ortho.png")

    heat_mesh.export(heat_mesh_path)

    heat_rgba = render_mesh(heat_mesh, heat_img_tmp, cam_cfg, width=width, height=height)
    save_heatmap_figure(
        heat_rgba,
        heat_img_final,
        norm,
        cmap,
        label="GT vertex distance to aligned RM"
    )

    if os.path.exists(heat_img_tmp):
        os.remove(heat_img_tmp)

    print("[7/7] Saving outputs...")

    rm_aligned_export = rm_aligned.copy()
    rm_aligned_export.apply_scale(1.0 / internal_scale)
    aligned_path = os.path.join(paths["aligned"], "rm_aligned.ply")
    rm_aligned_export.export(aligned_path)

    df = pd.DataFrame([{
        "gt_file": os.path.abspath(gt_path),
        "rm_file": os.path.abspath(rm_path),

        "alignment_triggered": alignment_triggered,
        "mse_threshold_normalized": mse_threshold_normalized,

        "pre_alignment_mse_normalized": pre_mse_norm,
        "post_alignment_mse_normalized": post_mse_norm,

        "pre_alignment_mse_gt_units_sq": pre_mse_gt_units_sq,
        "post_alignment_mse_gt_units_sq": post_mse_gt_units_sq,

        "mean_chamfer_normalized": metrics["chamfer_mean"],
        "symmetric_hausdorff_normalized": metrics["hausdorff"],
        "symmetric_rmse_normalized": metrics["rmse"],

        "mean_chamfer_gt_units": chamfer_gt_units,
        "symmetric_hausdorff_gt_units": hausdorff_gt_units,
        "symmetric_rmse_gt_units": rmse_gt_units,

        "gt_bbox_diagonal_original_units": gt_diag_raw,
        "camera_azimuth_deg": azimuth_deg,
        "camera_elevation_deg": elevation_deg,
        "final_transform_00": final_transform[0, 0],
        "final_transform_01": final_transform[0, 1],
        "final_transform_02": final_transform[0, 2],
        "final_transform_03": final_transform[0, 3],
        "final_transform_10": final_transform[1, 0],
        "final_transform_11": final_transform[1, 1],
        "final_transform_12": final_transform[1, 2],
        "final_transform_13": final_transform[1, 3],
        "final_transform_20": final_transform[2, 0],
        "final_transform_21": final_transform[2, 1],
        "final_transform_22": final_transform[2, 2],
        "final_transform_23": final_transform[2, 3],
    }])

    csv_path = os.path.join(paths["metrics"], "mesh_metrics.csv")
    df.to_csv(csv_path, index=False)

    print("\nDone.")
    print(f"GT render:        {gt_render_path}")
    print(f"RM render:        {rm_render_path}")
    print(f"Heatmap image:    {heat_img_final}")
    print(f"Heatmap mesh:     {heat_mesh_path}")
    print(f"Aligned RM mesh:  {aligned_path}")
    print(f"Metrics CSV:      {csv_path}")


# ============================================================
# CLI
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(description="GT/RM STL mesh evaluation pipeline")
    parser.add_argument("--gt", required=True, help="Path to ground-truth STL")
    parser.add_argument("--rm", required=True, help="Path to reconstructed-model STL")
    parser.add_argument("--out", default="output", help="Output directory")

    parser.add_argument("--mse-threshold", type=float, default=1e-4,
                        help="Normalized symmetric MSE threshold to trigger similarity ICP")
    parser.add_argument("--azimuth", type=float, default=-135.0,
                        help="Orthographic camera azimuth in degrees")
    parser.add_argument("--elevation", type=float, default=25.264,
                        help="Orthographic camera elevation in degrees")
    parser.add_argument("--width", type=int, default=1600, help="Render width")
    parser.add_argument("--height", type=int, default=1200, help="Render height")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        gt_path=args.gt,
        rm_path=args.rm,
        out_dir=args.out,
        mse_threshold_normalized=args.mse_threshold,
        azimuth_deg=args.azimuth,
        elevation_deg=args.elevation,
        width=args.width,
        height=args.height
    )