"""Qt-free grouping of a run's images into GT/RM pairs for the results gallery."""
import glob
import os
import re

_VIEW_RE = re.compile(r"^gt_view(\d+)\.png$")


def collect_image_entries(out_dir):
    """
    Return ``[(title, [(caption, path), ...]), ...]`` for the images under ``out_dir``.

    Each entry holds one image or a GT/RM pair taken from the same camera angle: the geometric
    render, the deviation heatmap (single image) and every saved perceptual view.
    """
    def path(*parts):
        return os.path.join(out_dir, *parts)

    entries = []

    geometric = [("GT", path("renders", "gt_ortho.png")), ("RM aligned", path("renders", "rm_aligned_ortho.png"))]
    geometric = [(caption, p) for caption, p in geometric if os.path.isfile(p)]
    if geometric:
        entries.append(("Geometric view", geometric))

    heatmap = path("heatmaps", "gt_heatmap_ortho.png")
    if os.path.isfile(heatmap):
        entries.append(("Deviation heatmap", [("GT vertex distance to aligned RM", heatmap)]))

    gt_dir = path("renders", "gt")
    views = []
    for p in glob.glob(os.path.join(gt_dir, "gt_view*.png")):
        match = _VIEW_RE.match(os.path.basename(p))
        if match:
            views.append((int(match.group(1)), match.group(1), p))
    for _, number, gt_path in sorted(views):
        pair = [("GT", gt_path)]
        rm_path = path("renders", "rm", f"rm_view{number}.png")
        if os.path.isfile(rm_path):
            pair.append(("RM aligned", rm_path))
        entries.append((f"Perceptual view {number}", pair))

    return entries
