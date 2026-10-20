import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


ROBUST_PERCENTILE = 95  # distances above this percentile share the top colour


def colorize_gt_heatmap(gt_mesh, d_gt2rm, cmap_name="RdYlGn_r", robust_percentile=ROBUST_PERCENTILE):
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
