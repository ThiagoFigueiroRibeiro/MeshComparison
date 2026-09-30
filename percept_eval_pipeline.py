import os
import argparse
import numpy as np
import pandas as pd
import trimesh
import pyrender
import open3d as o3d
import matplotlib.pyplot as plt
import imageio.v2 as imageio

from scipy.spatial import cKDTree
from skimage.metrics import structural_similarity as skimage_ssim

import torch
import lpips


# ============================================================
# Utilities
# ============================================================

def ensure_dirs(base_out):
    paths = {
        "renders_gt": os.path.join(base_out, "renders", "gt"),
        "renders_rm": os.path.join(base_out, "renders", "rm"),
        "renders_pairs": os.path.join(base_out, "renders", "pairs"),
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
# Mesh Loader
# ============================================================

def load_mesh(path):
    """
    Loads STL/OBJ/PLY/etc. using trimesh.
    FBX is not supported.
    """
    ext = os.path.splitext(path)[1].lower()

    if ext == ".fbx":
        raise ValueError(
            f"FBX is not supported in this pipeline: {path}\n"
            f"Please convert FBX -> STL first."
        )

    try:
        loaded = trimesh.load(path, force='scene', process=False, maintain_order=True)

        if isinstance(loaded, trimesh.Trimesh):
            mesh = loaded.copy()

        elif isinstance(loaded, trimesh.Scene):
            meshes = []
            for name, geom in loaded.geometry.items():
                for node_name in loaded.graph.nodes_geometry:
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
# Metrics on vertices
# ============================================================

def symmetric_vertex_errors(gt_vertices, rm_vertices):
    d_gt2rm, _ = nn_distances(gt_vertices, rm_vertices)
    d_rm2gt, _ = nn_distances(rm_vertices, gt_vertices)
    return d_gt2rm, d_rm2gt


def symmetric_mse(gt_vertices, rm_vertices):
    d_gt2rm, d_rm2gt = symmetric_vertex_errors(gt_vertices, rm_vertices)
    mse = 0.5 * (np.mean(d_gt2rm ** 2) + np.mean(d_rm2gt ** 2))
    return mse


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

def camera_pose_for_view(center, diag, azimuth_deg, elevation_deg, radius_factor=1.45):
    """
    Camera position for a given view angle.
    Radius is intentionally not too large so the object stays visually large.
    """
    az = np.deg2rad(azimuth_deg)
    el = np.deg2rad(elevation_deg)
    radius = radius_factor * diag

    eye = center + radius * np.array([
        np.cos(el) * np.cos(az),
        np.cos(el) * np.sin(az),
        np.sin(el)
    ])
    return look_at(eye, center, up=np.array([0.0, 0.0, 1.0]))


def build_tight_ortho_camera(meshes, camera_pose, margin=1.05):
    """
    Compute xmag/ymag by projecting the global bounding box corners into
    the current camera frame. This gives a tighter orthographic framing.
    """
    all_vertices = np.vstack([m.vertices for m in meshes])
    mn = all_vertices.min(axis=0)
    mx = all_vertices.max(axis=0)
    bbox = np.array([mn, mx], dtype=np.float64)

    corners_world = bounds_corners(bbox)
    view = np.linalg.inv(camera_pose)
    corners_cam = apply_transform_points(corners_world, view)

    xmag = np.max(np.abs(corners_cam[:, 0])) * margin
    ymag = np.max(np.abs(corners_cam[:, 1])) * margin

    diag = np.linalg.norm(mx - mn) + 1e-12
    zfar = max(10.0 * diag, 10.0)

    center = 0.5 * (mn + mx)
    return {
        "pose": camera_pose,
        "xmag": float(xmag),
        "ymag": float(ymag),
        "zfar": float(zfar),
        "center": center,
        "diag": float(diag),
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


def render_mesh_rgba(mesh, camera_cfg, width=1600, height=1200, smooth=True):
    scene = pyrender.Scene(
        bg_color=np.array([0, 0, 0, 0], dtype=np.float32),
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

    return color


def rgba_to_rgb_mask(rgba):
    rgb = rgba[:, :, :3].astype(np.float32) / 255.0
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0
    mask = alpha > 0.0
    rgb_masked = rgb * alpha[..., None]
    return rgb_masked, alpha, mask


def crop_to_union_mask(img1, img2, mask1, mask2, pad=12):
    union = mask1 | mask2
    ys, xs = np.where(union)
    if len(xs) == 0 or len(ys) == 0:
        raise ValueError("Union mask is empty; nothing was rendered.")

    h, w = union.shape
    x0 = max(int(xs.min()) - pad, 0)
    y0 = max(int(ys.min()) - pad, 0)
    x1 = min(int(xs.max()) + pad + 1, w)
    y1 = min(int(ys.max()) + pad + 1, h)

    img1_c = img1[y0:y1, x0:x1]
    img2_c = img2[y0:y1, x0:x1]
    mask1_c = mask1[y0:y1, x0:x1]
    mask2_c = mask2[y0:y1, x0:x1]
    union_c = union[y0:y1, x0:x1]

    return img1_c, img2_c, mask1_c, mask2_c, union_c


# ============================================================
# Perceptual Metrics
# ============================================================

def masked_psnr(gt_img, rm_img, mask):
    """
    PSNR over masked pixels only.
    Images are float32 in [0,1].
    """
    mask3 = mask[..., None].astype(np.float32)
    denom = np.sum(mask3)
    if denom <= 0:
        return np.nan

    mse = np.sum(((gt_img - rm_img) ** 2) * mask3) / (denom + 1e-12)
    if mse <= 1e-12:
        return np.inf
    return 10.0 * np.log10(1.0 / mse)


def masked_ssim(gt_img, rm_img):
    """
    SSIM on a masked crop where background has already been zeroed.
    """
    return skimage_ssim(
        gt_img,
        rm_img,
        channel_axis=-1,
        data_range=1.0
    )


def masked_lpips(lpips_model, gt_img, rm_img, device):
    """
    LPIPS on masked crop with background zeroed.
    """
    gt_t = torch.from_numpy(gt_img).permute(2, 0, 1).unsqueeze(0).to(device=device, dtype=torch.float32)
    rm_t = torch.from_numpy(rm_img).permute(2, 0, 1).unsqueeze(0).to(device=device, dtype=torch.float32)

    gt_t = gt_t * 2.0 - 1.0
    rm_t = rm_t * 2.0 - 1.0

    with torch.no_grad():
        val = lpips_model(gt_t, rm_t)
    return float(val.item())


def summarize_stats(values):
    arr = np.asarray(values, dtype=np.float64)
    finite = arr[np.isfinite(arr)]

    if len(finite) == 0:
        return {
            "min": np.nan, "max": np.nan, "p25": np.nan, "p75": np.nan,
            "median": np.nan, "mean": np.nan
        }

    return {
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
        "p25": float(np.percentile(finite, 25)),
        "p75": float(np.percentile(finite, 75)),
        "median": float(np.median(finite)),
        "mean": float(np.mean(finite)),
    }


def save_pair_figure(gt_img, rm_img, out_path, title_left="GT", title_right="RM"):
    fig, axes = plt.subplots(1, 2, figsize=(14, 7), dpi=150)

    axes[0].imshow(gt_img)
    axes[0].set_title(title_left)
    axes[0].axis("off")

    axes[1].imshow(rm_img)
    axes[1].set_title(title_right)
    axes[1].axis("off")

    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


# ============================================================
# Main Pipeline
# ============================================================

def run_pipeline(gt_path, rm_path, out_dir,
                 mse_threshold_normalized=1e-4,
                 elevation_deg=25.264,
                 width=1600,
                 height=1200,
                 num_views=100,
                 save_views=(1, 33, 66),
                 camera_margin=1.05,
                 radius_factor=1.45):

    paths = ensure_dirs(out_dir)

    print("[1/8] Loading meshes...")
    gt_raw = load_mesh(gt_path)
    rm_raw = load_mesh(rm_path)

    print("[2/8] Internal scale normalization...")
    gt = gt_raw.copy()
    rm = rm_raw.copy()

    gt_diag_raw = np.linalg.norm(gt.bounds[1] - gt.bounds[0])
    if gt_diag_raw < 1e-12:
        raise ValueError("GT mesh bounding-box diagonal is too small.")

    internal_scale = 1.0 / gt_diag_raw
    gt.apply_scale(internal_scale)
    rm.apply_scale(internal_scale)

    print("[3/8] Computing pre-alignment MSE...")
    pre_mse_norm = symmetric_mse(gt.vertices, rm.vertices)
    alignment_triggered = pre_mse_norm > mse_threshold_normalized

    print(f"    Pre-alignment symmetric MSE (normalized): {pre_mse_norm:.8e}")
    print(f"    Threshold (normalized): {mse_threshold_normalized:.8e}")
    print(f"    Alignment triggered: {alignment_triggered}")

    rm_aligned = rm.copy()
    final_transform = np.eye(4)

    if alignment_triggered:
        print("[4/8] Running similarity ICP alignment (RM -> GT)...")
        T, fitness, inlier_rmse = similarity_icp_align(
            rm.vertices,
            gt.vertices
        )
        rm_aligned.apply_transform(T)
        final_transform = T
        print(f"    ICP fitness: {fitness:.6f}")
        print(f"    ICP inlier RMSE: {inlier_rmse:.6f}")
    else:
        print("[4/8] Alignment skipped.")

    print("[5/8] Preparing LPIPS model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        lpips_model = lpips.LPIPS(net="alex").to(device).eval()
    except Exception as e:
        raise RuntimeError(
            "LPIPS could not be initialized. Make sure it is installed:\n"
            "pip install lpips torch torchvision\n"
            f"Original error: {e}"
        )
    print(f"    LPIPS device: {device}")

    print("[6/8] Rendering 100 views and computing metrics...")
    per_view_rows = []
    save_views = set(save_views)
    azimuths = np.linspace(0.0, 360.0, num_views, endpoint=False)

    lpips_vals = []
    psnr_vals = []
    ssim_vals = []

    all_meshes = [gt, rm_aligned]
    center = 0.5 * (np.vstack([m.vertices for m in all_meshes]).min(axis=0) +
                    np.vstack([m.vertices for m in all_meshes]).max(axis=0))
    diag = np.linalg.norm(np.vstack([m.vertices for m in all_meshes]).max(axis=0) -
                          np.vstack([m.vertices for m in all_meshes]).min(axis=0)) + 1e-12

    for i, az in enumerate(azimuths, start=1):
        cam_pose = camera_pose_for_view(
            center=center,
            diag=diag,
            azimuth_deg=az,
            elevation_deg=elevation_deg,
            radius_factor=radius_factor
        )

        cam_cfg = build_tight_ortho_camera(
            [gt, rm_aligned],
            camera_pose=cam_pose,
            margin=camera_margin
        )

        gt_rgba = render_mesh_rgba(
            gt, cam_cfg, width=width, height=height
        )
        rm_rgba = render_mesh_rgba(
            rm_aligned, cam_cfg, width=width, height=height
        )

        gt_img, gt_alpha, gt_mask = rgba_to_rgb_mask(gt_rgba)
        rm_img, rm_alpha, rm_mask = rgba_to_rgb_mask(rm_rgba)

        # Crop to union of object regions so background does not dominate
        gt_crop, rm_crop, gt_mask_c, rm_mask_c, union_c = crop_to_union_mask(
            gt_img, rm_img, gt_mask, rm_mask, pad=12
        )

        # Zero background in the crop
        gt_crop_masked = gt_crop * union_c[..., None].astype(np.float32)
        rm_crop_masked = rm_crop * union_c[..., None].astype(np.float32)

        psnr_val = masked_psnr(gt_crop, rm_crop, union_c)
        ssim_val = masked_ssim(gt_crop_masked, rm_crop_masked)
        lpips_val = masked_lpips(lpips_model, gt_crop_masked, rm_crop_masked, device=device)

        lpips_vals.append(lpips_val)
        psnr_vals.append(psnr_val)
        ssim_vals.append(ssim_val)

        per_view_rows.append({
            "view_idx": i,
            "azimuth_deg": float(az),
            "elevation_deg": float(elevation_deg),
            "lpips": lpips_val,
            "psnr": psnr_val,
            "ssim": ssim_val,
            "crop_h": int(gt_crop.shape[0]),
            "crop_w": int(gt_crop.shape[1]),
            "xmag": float(cam_cfg["xmag"]),
            "ymag": float(cam_cfg["ymag"]),
        })

        if i in save_views:
            gt_save = os.path.join(paths["renders_gt"], f"gt_view{i:03d}.png")
            rm_save = os.path.join(paths["renders_rm"], f"rm_view{i:03d}.png")
            pair_save = os.path.join(paths["renders_pairs"], f"pair_view{i:03d}.png")

            imageio.imwrite(gt_save, (gt_img * 255).astype(np.uint8))
            imageio.imwrite(rm_save, (rm_img * 255).astype(np.uint8))
            save_pair_figure(gt_img, rm_img, pair_save, title_left=f"GT view {i}", title_right=f"RM view {i}")

            print(f"    Saved selected view {i:03d}")

        print(
            f"    View {i:03d}/{num_views} | az={az:7.2f} | "
            f"LPIPS={lpips_val:.5f} | PSNR={psnr_val:.3f} | SSIM={ssim_val:.5f}"
        )

    print("[7/8] Summarizing metrics...")

    lpips_stats = summarize_stats(lpips_vals)
    psnr_stats = summarize_stats(psnr_vals)
    ssim_stats = summarize_stats(ssim_vals)

    summary_rows = []
    for metric_name, stats in [
        ("lpips", lpips_stats),
        ("psnr", psnr_stats),
        ("ssim", ssim_stats),
    ]:
        summary_rows.append({
            "metric": metric_name,
            "min": stats["min"],
            "max": stats["max"],
            "p25": stats["p25"],
            "p75": stats["p75"],
            "median": stats["median"],
            "mean": stats["mean"],
        })

    per_view_df = pd.DataFrame(per_view_rows)
    summary_df = pd.DataFrame(summary_rows)

    per_view_csv = os.path.join(paths["metrics"], "per_view_metrics.csv")
    summary_csv = os.path.join(paths["metrics"], "metric_summary.csv")
    per_view_df.to_csv(per_view_csv, index=False)
    summary_df.to_csv(summary_csv, index=False)

    print("[8/8] Saving aligned mesh and metadata...")

    rm_aligned_export = rm_aligned.copy()
    rm_aligned_export.apply_scale(1.0 / internal_scale)
    aligned_path = os.path.join(paths["aligned"], "rm_aligned.ply")
    rm_aligned_export.export(aligned_path)

    meta_df = pd.DataFrame([{
        "gt_file": os.path.abspath(gt_path),
        "rm_file": os.path.abspath(rm_path),
        "alignment_triggered": alignment_triggered,
        "mse_threshold_normalized": mse_threshold_normalized,
        "pre_alignment_mse_normalized": pre_mse_norm,
        "gt_bbox_diagonal_original_units": gt_diag_raw,
        "camera_elevation_deg": elevation_deg,
        "num_views": num_views,
        "saved_views": ",".join(map(str, sorted(save_views))),
        "camera_margin": camera_margin,
        "radius_factor": radius_factor,
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
    meta_csv = os.path.join(paths["metrics"], "run_metadata.csv")
    meta_df.to_csv(meta_csv, index=False)

    print("\nDone.")
    print(f"GT renders:       {paths['renders_gt']}")
    print(f"RM renders:       {paths['renders_rm']}")
    print(f"Pair renders:     {paths['renders_pairs']}")
    print(f"Aligned RM mesh:  {aligned_path}")
    print(f"Per-view metrics: {per_view_csv}")
    print(f"Summary metrics:  {summary_csv}")
    print(f"Run metadata:     {meta_csv}")

    print("\nMetric summary:")
    print(summary_df.to_string(index=False))


# ============================================================
# CLI
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(description="GT/RM STL perceptual evaluation pipeline")
    parser.add_argument("--gt", required=True, help="Path to ground-truth STL")
    parser.add_argument("--rm", required=True, help="Path to reconstructed-model STL")
    parser.add_argument("--out", default="output", help="Output directory")

    parser.add_argument("--mse-threshold", type=float, default=1e-4,
                        help="Normalized symmetric MSE threshold to trigger similarity ICP")
    parser.add_argument("--elevation", type=float, default=25.264,
                        help="Fixed elevation in degrees")
    parser.add_argument("--width", type=int, default=1600, help="Render width")
    parser.add_argument("--height", type=int, default=1200, help="Render height")
    parser.add_argument("--num-views", type=int, default=100, help="Number of azimuth views")
    parser.add_argument("--save-views", nargs="+", type=int, default=[1, 33, 66],
                        help="1-based view indices to save as images")

    parser.add_argument("--camera-margin", type=float, default=1.05,
                        help="Margin for orthographic framing; smaller values make object larger")
    parser.add_argument("--radius-factor", type=float, default=1.45,
                        help="Camera distance as a multiple of bbox diagonal")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        gt_path=args.gt,
        rm_path=args.rm,
        out_dir=args.out,
        mse_threshold_normalized=args.mse_threshold,
        elevation_deg=args.elevation,
        width=args.width,
        height=args.height,
        num_views=args.num_views,
        save_views=args.save_views,
        camera_margin=args.camera_margin,
        radius_factor=args.radius_factor
    )