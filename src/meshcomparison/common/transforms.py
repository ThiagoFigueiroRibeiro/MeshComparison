import numpy as np


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
