import subprocess
import sys
from pathlib import Path

import pandas as pd

from meshcomparison.gui.config import RunConfig, build_commands

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples"


def test_geometry_worker_runs_from_the_gui_command(tmp_path):
    cfg = RunConfig(gt=str(SAMPLES / "gt.stl"), rm=str(SAMPLES / "mod.stl"), out=str(tmp_path / "out"),
                    run_perceptual=False, width=320, height=240)
    python, commands = build_commands(cfg, python=sys.executable)
    assert [c.name for c in commands] == ["Geometric"]

    result = subprocess.run([python, *commands[0].args], input=commands[0].stdin, text=True,
                            capture_output=True, timeout=300)

    assert result.returncode == 0, result.stderr
    assert "[7/7]" in result.stdout
    metrics = pd.read_csv(tmp_path / "out" / "metrics" / "metrics_geometry.csv")
    assert metrics["mean_chamfer_normalized"].iloc[0] > 0
    assert (tmp_path / "out" / "heatmaps" / "gt_heatmap_colored.ply").is_file()
