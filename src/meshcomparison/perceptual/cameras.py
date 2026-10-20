import numpy as np

from ..common.rendering import OrthoRenderer, render_ortho_rgba
from ..common.transforms import apply_transform_points, bounds_corners, look_at


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


TRANSPARENT_BACKGROUND = np.array([0, 0, 0, 0], dtype=np.float32)


def render_mesh_rgba(mesh, camera_cfg, width=1600, height=1200, smooth=True):
    return render_ortho_rgba(
        mesh, camera_cfg, TRANSPARENT_BACKGROUND, width=width, height=height, smooth=smooth
    )


def make_view_renderer(gt, rm_aligned, width=1600, height=1200):
    """One renderer (OpenGL context) with both meshes uploaded, for rendering many views quickly."""
    renderer = OrthoRenderer(TRANSPARENT_BACKGROUND, width=width, height=height)
    renderer.add_mesh("gt", gt)
    renderer.add_mesh("rm", rm_aligned)
    return renderer
