import imageio.v2 as imageio
import numpy as np

from ..common.rendering import render_ortho_rgba
from ..common.transforms import apply_transform_points, bounds_corners, look_at


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


def render_mesh(mesh, out_path, camera_cfg,
                width=1600, height=1200,
                bg_color=(255, 255, 255, 255),
                smooth=True):
    color = render_ortho_rgba(
        mesh, camera_cfg, np.array(bg_color) / 255.0,
        width=width, height=height, smooth=smooth
    )
    imageio.imwrite(out_path, color)
    return color
