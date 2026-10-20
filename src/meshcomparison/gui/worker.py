"""Internal entry point of the child processes started by the GUI: ``python -m meshcomparison.gui.worker``.

The window never imports the pipelines; each run is a separate process that receives the run
configuration (``RunConfig`` as JSON on standard input), so rendering stays isolated from the 3D viewer
and a run can be cancelled.
"""
import json
import sys
from dataclasses import fields

from .config import RunConfig

PIPELINES = ("geometry", "perceptual")


def config_from_json(payload):
    """Rebuild a ``RunConfig`` from the JSON written by ``config_to_json``, ignoring unknown keys."""
    data = json.loads(payload)
    known = {f.name for f in fields(RunConfig)}
    data = {key: value for key, value in data.items() if key in known}
    if "save_views" in data:
        data["save_views"] = tuple(data["save_views"])
    return RunConfig(**data)


def run_geometry(cfg):
    from ..geometry.pipeline import run_pipeline

    run_pipeline(
        gt_path=cfg.gt,
        rm_path=cfg.rm,
        out_dir=cfg.out,
        mse_threshold_normalized=cfg.mse_threshold,
        azimuth_deg=cfg.azimuth,
        elevation_deg=cfg.elevation,
        width=cfg.width,
        height=cfg.height,
    )


def run_perceptual(cfg):
    from ..perceptual.pipeline import run_pipeline

    run_pipeline(
        gt_path=cfg.gt,
        rm_path=cfg.rm,
        out_dir=cfg.out,
        mse_threshold_normalized=cfg.mse_threshold,
        elevation_deg=cfg.elevation,
        width=cfg.width,
        height=cfg.height,
        num_views=cfg.num_views,
        save_views=cfg.save_views,
        camera_margin=cfg.camera_margin,
        radius_factor=cfg.radius_factor,
        device=cfg.device,
    )


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or argv[0] not in PIPELINES:
        choices = "|".join(PIPELINES)
        print(f"usage: python -m meshcomparison.gui.worker {{{choices}}}  (run configuration JSON on stdin)",
              file=sys.stderr)
        return 2
    cfg = config_from_json(sys.stdin.read())
    {"geometry": run_geometry, "perceptual": run_perceptual}[argv[0]](cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
