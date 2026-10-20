import numpy as np
import trimesh

from meshcomparison.geometry.heatmap import colorize_gt_heatmap


def test_heatmap_scale_is_the_95th_percentile_of_the_distances():
    mesh = trimesh.creation.icosphere(subdivisions=1)
    distances = np.linspace(0.0, 1.0, len(mesh.vertices))
    heat_mesh, norm, _ = colorize_gt_heatmap(mesh, distances)
    assert norm.vmin == 0.0
    assert np.isclose(norm.vmax, np.percentile(distances, 95))
    assert heat_mesh.visual.vertex_colors.shape == (len(mesh.vertices), 4)
