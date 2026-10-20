import numpy as np
import pytest
import trimesh

pytest.importorskip("pyrender")

from meshcomparison.common.rendering import OrthoRenderer, render_ortho_rgba  # noqa: E402
from meshcomparison.perceptual.cameras import build_tight_ortho_camera, camera_pose_for_view  # noqa: E402

BACKGROUND = np.array([0, 0, 0, 0], dtype=np.float32)


def _cameras(mesh, azimuths):
    center, diag = mesh.bounds.mean(axis=0), float(np.linalg.norm(mesh.extents))
    return [build_tight_ortho_camera([mesh], camera_pose_for_view(center, diag, az, 25.264)) for az in azimuths]


def test_reused_renderer_matches_one_off_renders():
    mesh = trimesh.creation.icosphere(subdivisions=2)
    cameras = _cameras(mesh, (0.0, 90.0, 200.0))
    try:
        renderer = OrthoRenderer(BACKGROUND, width=96, height=72)
    except Exception as exc:  # no offscreen OpenGL available (headless machine)
        pytest.skip(f"offscreen rendering unavailable: {exc}")
    with renderer:
        renderer.add_mesh("sphere", mesh)
        reused = [renderer.render("sphere", camera) for camera in cameras]

    for camera, image in zip(cameras, reused):
        expected = render_ortho_rgba(mesh, camera, BACKGROUND, width=96, height=72)
        assert np.array_equal(image, expected)
