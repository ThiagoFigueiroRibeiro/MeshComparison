import subprocess
import sys
from pathlib import Path

import pandas as pd

from meshcomparison.gui.config import RunConfig, build_commands

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "data" / "samples"
ORIGINAL = ROOT / "examples" / "output" / "metrics"  # record of a run of the original pipelines


def _run(cfg):
    python, commands = build_commands(cfg, python=sys.executable)
    for command in commands:
        result = subprocess.run([python, *command.args], input=command.stdin, text=True,
                                capture_output=True, timeout=600)
        assert result.returncode == 0, result.stderr


def _columns(path):
    return list(pd.read_csv(path).columns)


def test_geometric_outputs_match_the_original_schema(tmp_path):
    cfg = RunConfig(gt=str(SAMPLES / "gt.stl"), rm=str(SAMPLES / "mod.stl"), out=str(tmp_path),
                    run_perceptual=False, width=320, height=240)
    _run(cfg)

    # the original geometric pipeline writes a single CSV
    assert sorted(p.name for p in (tmp_path / "metrics").iterdir()) == ["metrics_geometry.csv"]
    assert _columns(tmp_path / "metrics" / "metrics_geometry.csv") == _columns(ORIGINAL / "metrics_geometry.csv")


def test_perceptual_outputs_match_the_original_schema(tmp_path):
    cfg = RunConfig(gt=str(SAMPLES / "gt.stl"), rm=str(SAMPLES / "mod.stl"), out=str(tmp_path),
                    run_geometry=False, width=320, height=240, num_views=2, save_views=(1, 2), device="cpu")
    _run(cfg)

    names = ("metrics_perceptual.csv", "per_view_metrics.csv", "run_metadata.csv")
    assert sorted(p.name for p in (tmp_path / "metrics").iterdir()) == sorted(names)
    for name in names:
        assert _columns(tmp_path / "metrics" / name) == _columns(ORIGINAL / name), name
