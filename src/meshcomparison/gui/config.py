"""Qt-free logic of the GUI: run configuration, validation, command lines and progress parsing."""
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field

from ..common.device import DEVICE_CHOICES

MESH_FILE_FILTER = (
    "Meshes (*.stl *.obj *.ply *.off *.glb *.gltf);;STL (*.stl);;OBJ (*.obj);;PLY (*.ply);;All files (*)"
)

_STEP_RE = re.compile(r"^\s*\[(\d+)/(\d+)\]")
_VIEW_RE = re.compile(r"^\s*View\s+(\d+)/(\d+)\b")


@dataclass
class RunConfig:
    gt: str = ""
    rm: str = ""
    out: str = "output"
    run_geometry: bool = True
    run_perceptual: bool = True
    mse_threshold: float = 1e-4
    azimuth: float = -135.0
    elevation: float = 25.264
    width: int = 1600
    height: int = 1200
    num_views: int = 100
    save_views: tuple = (1, 33, 66)
    camera_margin: float = 1.05
    radius_factor: float = 1.45
    device: str = "auto"


@dataclass
class Command:
    name: str
    args: list = field(default_factory=list)
    stdin: str = ""  # run configuration (JSON) written to the child's standard input


def validate(cfg):
    """Return a list of human-readable problems with ``cfg`` (empty when it can be run)."""
    errors = []
    for label, path in (("Ground truth (GT)", cfg.gt), ("Reconstructed mesh (RM)", cfg.rm)):
        if not path:
            errors.append(f"{label}: no file selected.")
        elif os.path.splitext(path)[1].lower() == ".fbx":
            errors.append(f"{label}: FBX is not supported. Convert it to STL, OBJ or PLY first.")
        elif not os.path.isfile(path):
            errors.append(f"{label}: file not found: {path}")
    if not (cfg.run_geometry or cfg.run_perceptual):
        errors.append("Select at least one pipeline.")
    if not cfg.out:
        errors.append("Output folder: not set.")
    if cfg.width < 16 or cfg.height < 16:
        errors.append("Render width and height must be at least 16 pixels.")
    if cfg.run_perceptual and cfg.num_views < 1:
        errors.append("Number of views must be at least 1.")
    if cfg.device not in DEVICE_CHOICES:
        errors.append(f"Unknown device: {cfg.device}")
    return errors


def config_to_json(cfg):
    return json.dumps(asdict(cfg))


def build_commands(cfg, python=None):
    """Child-process command lines (``meshcomparison.gui.worker``) for the selected pipelines, in run order."""
    python = python or sys.executable
    payload = config_to_json(cfg)
    commands = []
    if cfg.run_geometry:
        commands.append(Command("Geometric", ["-u", "-m", "meshcomparison.gui.worker", "geometry"], payload))
    if cfg.run_perceptual:
        commands.append(Command("Perceptual", ["-u", "-m", "meshcomparison.gui.worker", "perceptual"], payload))
    return python, commands


class ProgressTracker:
    """Turns the ``[n/N]`` step markers and ``View i/V`` lines printed by the pipelines into a 0-1 fraction."""

    def __init__(self, n_commands):
        self.n_commands = max(1, n_commands)
        self.command_index = 0
        self.step = 0
        self.total_steps = 1
        self.view_fraction = 0.0

    def start_command(self, index):
        self.command_index = index
        self.step = 0
        self.view_fraction = 0.0

    def feed(self, line):
        m = _STEP_RE.match(line)
        if m:
            self.step, self.total_steps = int(m.group(1)), int(m.group(2))
            self.view_fraction = 0.0
            return
        m = _VIEW_RE.match(line)
        if m and int(m.group(2)) > 0:
            self.view_fraction = int(m.group(1)) / int(m.group(2))

    @property
    def fraction(self):
        within = 0.0
        if self.step:
            within = (self.step - 1 + self.view_fraction) / self.total_steps
        return min(1.0, (self.command_index + within) / self.n_commands)

    def finish_command(self):
        self.step, self.view_fraction = self.total_steps, 0.0
        self.command_index += 1
        self.step = 0
