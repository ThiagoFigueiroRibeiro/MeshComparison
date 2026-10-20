import collections
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import imageio.v2 as imageio
import numpy as np
import pandas as pd

from ..common.device import get_device_info
from ..common.io import ensure_dirs
from ..common.prepare import export_aligned, prepare_meshes, transform_columns
from .cameras import build_tight_ortho_camera, camera_pose_for_view, make_view_renderer
from .figures import save_pair_figure
from .image_metrics import (
    crop_to_union_mask,
    masked_lpips,
    masked_psnr,
    masked_ssim,
    rgba_to_rgb_mask,
    summarize_stats,
)

TOTAL_STEPS = 8
METRIC_WORKERS = 2  # threads computing PSNR/SSIM/LPIPS while the main thread renders
MAX_PENDING_VIEWS = 3  # rendered views waiting for metrics (each keeps two full-size images in memory)

OUTPUT_SUBDIRS = {
    "renders_gt": ("renders", "gt"),
    "renders_rm": ("renders", "rm"),
    "renders_pairs": ("renders", "pairs"),
    "metrics": ("metrics",),
    "aligned": ("aligned",),
}


def _load_lpips(device):
    """LPIPS (AlexNet) on the requested device; returns ``(model, device_info)``."""
    import lpips

    device_info = get_device_info(device)
    if device_info.warning:
        print(f"    WARNING: {device_info.warning}")
    try:
        model = lpips.LPIPS(net="alex").to(device_info.device).eval()
    except Exception as e:
        raise RuntimeError(
            "LPIPS could not be initialized. Make sure it is installed:\n"
            "pip install lpips torch torchvision\n"
            f"Original error: {e}"
        )
    print(f"    LPIPS device: {device_info.describe()}")
    return model, device_info


def _scene_framing(meshes):
    """Centre and bounding-box diagonal of all meshes together (used to place the cameras)."""
    vertices = np.vstack([m.vertices for m in meshes])
    low, high = vertices.min(axis=0), vertices.max(axis=0)
    return 0.5 * (low + high), np.linalg.norm(high - low) + 1e-12


def _render_view(renderer, gt, rm_aligned, azimuth, center, diag, elevation_deg, radius_factor, camera_margin):
    """Render GT and RM from one azimuth (OpenGL: must run on the thread that owns the renderer)."""
    cam_pose = camera_pose_for_view(
        center=center, diag=diag, azimuth_deg=azimuth, elevation_deg=elevation_deg, radius_factor=radius_factor)
    cam_cfg = build_tight_ortho_camera([gt, rm_aligned], camera_pose=cam_pose, margin=camera_margin)

    gt_img, gt_alpha, gt_mask = rgba_to_rgb_mask(renderer.render("gt", cam_cfg))
    rm_img, rm_alpha, rm_mask = rgba_to_rgb_mask(renderer.render("rm", cam_cfg))
    return {"gt_img": gt_img, "rm_img": rm_img, "gt_mask": gt_mask, "rm_mask": rm_mask, "cam_cfg": cam_cfg}


def _view_metrics(view, lpips_model, lpips_lock, device):
    """PSNR, SSIM and LPIPS of a rendered view (CPU/GPU work that can overlap with the next render)."""
    # Crop to union of object regions so background does not dominate
    gt_crop, rm_crop, gt_mask_c, rm_mask_c, union_c = crop_to_union_mask(
        view["gt_img"], view["rm_img"], view["gt_mask"], view["rm_mask"], pad=12)

    # Zero background in the crop
    gt_crop_masked = gt_crop * union_c[..., None].astype(np.float32)
    rm_crop_masked = rm_crop * union_c[..., None].astype(np.float32)

    with lpips_lock:  # one network call at a time (GPU memory / CPU threads)
        lpips_value = masked_lpips(lpips_model, gt_crop_masked, rm_crop_masked, device=device)
    return {
        "crop_shape": gt_crop.shape,
        "psnr": masked_psnr(gt_crop, rm_crop, union_c),
        "ssim": masked_ssim(gt_crop_masked, rm_crop_masked),
        "lpips": lpips_value,
    }


def _evaluate_views(renderer, gt, rm_aligned, azimuths, center, diag, elevation_deg, radius_factor,
                    camera_margin, lpips_model, device, on_rendered):
    """
    Yield ``(index, azimuth, view, metrics)`` in view order.

    Rendering stays on this thread (OpenGL); each rendered view's metrics are computed in worker threads
    while the next view renders. ``on_rendered(index, view)`` runs on this thread right after rendering.
    """
    lpips_lock = threading.Lock()
    pending = collections.deque()

    def collect(item):
        index, azimuth, view, future = item
        return index, azimuth, view, future.result()

    with ThreadPoolExecutor(max_workers=METRIC_WORKERS) as pool:
        for i, az in enumerate(azimuths, start=1):
            view = _render_view(renderer, gt, rm_aligned, az, center, diag, elevation_deg, radius_factor,
                                camera_margin)
            on_rendered(i, view)
            pending.append((i, az, view, pool.submit(_view_metrics, view, lpips_model, lpips_lock, device)))
            if len(pending) > MAX_PENDING_VIEWS:
                yield collect(pending.popleft())
        while pending:
            yield collect(pending.popleft())


def _save_view_images(index, gt_img, rm_img, paths):
    gt_save = os.path.join(paths["renders_gt"], f"gt_view{index:03d}.png")
    rm_save = os.path.join(paths["renders_rm"], f"rm_view{index:03d}.png")
    pair_save = os.path.join(paths["renders_pairs"], f"pair_view{index:03d}.png")

    imageio.imwrite(gt_save, (gt_img * 255).astype(np.uint8))
    imageio.imwrite(rm_save, (rm_img * 255).astype(np.uint8))
    save_pair_figure(gt_img, rm_img, pair_save, title_left=f"GT view {index}", title_right=f"RM view {index}")
    print(f"    Saved selected view {index:03d}")


def _summary_table(lpips_vals, psnr_vals, ssim_vals):
    rows = []
    for metric_name, values in (("lpips", lpips_vals), ("psnr", psnr_vals), ("ssim", ssim_vals)):
        stats = summarize_stats(values)
        rows.append({
            "metric": metric_name,
            "min": stats["min"],
            "max": stats["max"],
            "p25": stats["p25"],
            "p75": stats["p75"],
            "median": stats["median"],
            "mean": stats["mean"],
        })
    return pd.DataFrame(rows)


def _metadata_row(gt_path, rm_path, prepared, mse_threshold_normalized, elevation_deg, num_views, save_views,
                  camera_margin, radius_factor):
    return {
        "gt_file": os.path.abspath(gt_path),
        "rm_file": os.path.abspath(rm_path),
        "alignment_triggered": prepared.alignment_triggered,
        "mse_threshold_normalized": mse_threshold_normalized,
        "pre_alignment_mse_normalized": prepared.pre_mse_norm,
        "gt_bbox_diagonal_original_units": prepared.gt_diag_raw,
        "camera_elevation_deg": elevation_deg,
        "num_views": num_views,
        "saved_views": ",".join(map(str, sorted(save_views))),
        "camera_margin": camera_margin,
        "radius_factor": radius_factor,
        **transform_columns(prepared.final_transform),
    }


def run_pipeline(gt_path, rm_path, out_dir,
                 mse_threshold_normalized=1e-4,
                 elevation_deg=25.264,
                 width=1600,
                 height=1200,
                 num_views=100,
                 save_views=(1, 33, 66),
                 camera_margin=1.05,
                 radius_factor=1.45,
                 device="auto"):

    paths = ensure_dirs(out_dir, OUTPUT_SUBDIRS)

    prepared = prepare_meshes(gt_path, rm_path, mse_threshold_normalized, TOTAL_STEPS)
    gt, rm_aligned = prepared.gt, prepared.rm_aligned

    print(f"[5/{TOTAL_STEPS}] Preparing LPIPS model...")
    lpips_model, device_info = _load_lpips(device)

    print(f"[6/{TOTAL_STEPS}] Rendering {num_views} views and computing metrics...")
    save_views = set(save_views)

    azimuths = np.linspace(0.0, 360.0, num_views, endpoint=False)
    center, diag = _scene_framing([gt, rm_aligned])

    per_view_rows = []
    lpips_vals, psnr_vals, ssim_vals = [], [], []

    def save_if_selected(index, view):
        if index in save_views:
            _save_view_images(index, view["gt_img"], view["rm_img"], paths)

    with make_view_renderer(gt, rm_aligned, width=width, height=height) as renderer:
        results = _evaluate_views(
            renderer, gt, rm_aligned, azimuths, center, diag, elevation_deg, radius_factor, camera_margin,
            lpips_model, device_info.device, save_if_selected)
        for i, az, view, metrics in results:
            lpips_vals.append(metrics["lpips"])
            psnr_vals.append(metrics["psnr"])
            ssim_vals.append(metrics["ssim"])

            per_view_rows.append({
                "view_idx": i,
                "azimuth_deg": float(az),
                "elevation_deg": float(elevation_deg),
                "lpips": metrics["lpips"],
                "psnr": metrics["psnr"],
                "ssim": metrics["ssim"],
                "crop_h": int(metrics["crop_shape"][0]),
                "crop_w": int(metrics["crop_shape"][1]),
                "xmag": float(view["cam_cfg"]["xmag"]),
                "ymag": float(view["cam_cfg"]["ymag"]),
            })

            print(
                f"    View {i:03d}/{num_views} | az={az:7.2f} | "
                f"LPIPS={metrics['lpips']:.5f} | PSNR={metrics['psnr']:.3f} | SSIM={metrics['ssim']:.5f}"
            )

    print(f"[7/{TOTAL_STEPS}] Summarizing metrics...")
    summary_df = _summary_table(lpips_vals, psnr_vals, ssim_vals)

    per_view_csv = os.path.join(paths["metrics"], "per_view_metrics.csv")
    summary_csv = os.path.join(paths["metrics"], "metrics_perceptual.csv")
    pd.DataFrame(per_view_rows).to_csv(per_view_csv, index=False)
    summary_df.to_csv(summary_csv, index=False)

    print(f"[8/{TOTAL_STEPS}] Saving aligned mesh and metadata...")
    aligned_path = export_aligned(prepared, paths["aligned"])

    meta_csv = os.path.join(paths["metrics"], "run_metadata.csv")
    pd.DataFrame([_metadata_row(
        gt_path, rm_path, prepared, mse_threshold_normalized, elevation_deg, num_views, save_views,
        camera_margin, radius_factor)]).to_csv(meta_csv, index=False)

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
