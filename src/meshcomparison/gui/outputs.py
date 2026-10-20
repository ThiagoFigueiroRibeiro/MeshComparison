"""Qt-free reading of what a finished run wrote to its output folder, for the 3D view."""
import os
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from ..common.distances import nn_distances
from ..common.io import load_mesh
from ..geometry.heatmap import ROBUST_PERCENTILE


@dataclass
class RunMeshes:
    gt: object
    rm_aligned: Optional[object] = None
    heatmap: Optional[object] = None
    heatmap_scale: float = 1.0  # the heatmap mesh is saved with the GT bounding-box diagonal normalized to 1
    heatmap_vmax: Optional[float] = None  # colour-scale maximum in GT units (legend)


def _first_value(csv_path, column):
    """First value of ``column`` in ``csv_path``, or ``None`` if the file or the column is missing."""
    if not os.path.isfile(csv_path):
        return None
    table = pd.read_csv(csv_path)
    return float(table[column].iloc[0]) if column in table else None


def heatmap_range(gt, rm_aligned):
    """Upper end of the heatmap colour scale in GT units, recomputed from the saved meshes (the pipeline
    writes only the coloured mesh): the robust percentile of the GT-vertex to aligned-RM distances."""
    distances, _ = nn_distances(gt.vertices, rm_aligned.vertices)
    return float(np.nanpercentile(distances, ROBUST_PERCENTILE))


def load_run_meshes(gt_path, out_dir, with_heatmap):
    """GT, aligned RM and (when the geometric pipeline ran) heatmap mesh with its scale and legend range."""
    metrics = os.path.join(out_dir, "metrics")
    aligned = os.path.join(out_dir, "aligned", "rm_aligned.ply")
    heatmap_path = os.path.join(out_dir, "heatmaps", "gt_heatmap_colored.ply")

    result = RunMeshes(gt=load_mesh(gt_path), rm_aligned=load_mesh(aligned) if os.path.isfile(aligned) else None)
    if with_heatmap and os.path.isfile(heatmap_path):
        result.heatmap = load_mesh(heatmap_path)
        for csv in ("metrics_geometry.csv", "run_metadata.csv"):
            scale = _first_value(os.path.join(metrics, csv), "gt_bbox_diagonal_original_units")
            if scale is not None:
                result.heatmap_scale = scale
                break
        if result.rm_aligned is not None:
            result.heatmap_vmax = heatmap_range(result.gt, result.rm_aligned)
    return result
