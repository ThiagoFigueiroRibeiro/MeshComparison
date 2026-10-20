"""Side-panel building blocks of the main window: meshes, pipelines, fixed parameters and compute device."""
import json
import os
import sys

from PySide6.QtCore import QProcess, QSettings, Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from ..common.device import CUDA_INSTALL_COMMAND, DeviceInfo
from .config import MESH_FILE_FILTER, RunConfig


def _card(title):
    box = QGroupBox(title)
    box.setObjectName("card")
    return box


class FileField(QWidget):
    def __init__(self, caption, directory=False, parent=None):
        super().__init__(parent)
        self._caption = caption
        self._directory = directory
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("Select…")
        button = QPushButton("Browse…")
        button.clicked.connect(self._browse)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.edit, 1)
        layout.addWidget(button)

    def text(self):
        return self.edit.text().strip()

    def setText(self, value):
        self.edit.setText(value)

    def _browse(self):
        start = self.text() or QSettings().value("last_dir", "")
        if self._directory:
            path = QFileDialog.getExistingDirectory(self, self._caption, start)
        else:
            path, _ = QFileDialog.getOpenFileName(self, self._caption, start, MESH_FILE_FILTER)
        if path:
            QSettings().setValue("last_dir", os.path.dirname(path) if not self._directory else path)
            self.edit.setText(path)


class MeshesPanel(QGroupBox):
    """GT / RM / output-folder pickers. ``meshChanged('gt' | 'rm')`` fires when a path is entered or chosen."""

    meshChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__("Meshes", parent)
        self.setObjectName("card")
        form = QFormLayout(self)
        form.setHorizontalSpacing(8)
        form.setVerticalSpacing(6)
        self.gt_field = FileField("Select ground-truth mesh")
        self.rm_field = FileField("Select reconstructed mesh")
        self.out_field = FileField("Select output folder", directory=True)
        self.out_field.setText(os.path.abspath("output"))
        form.addRow("Ground truth (GT)", self.gt_field)
        form.addRow("Reconstruction (RM)", self.rm_field)
        form.addRow("Output folder", self.out_field)
        note = QLabel("STL, OBJ, PLY, OFF, GLB/GLTF. FBX is not supported: convert it first.")
        note.setObjectName("hint")
        note.setWordWrap(True)
        form.addRow(note)
        self.gt_field.edit.editingFinished.connect(lambda: self.meshChanged.emit("gt"))
        self.rm_field.edit.editingFinished.connect(lambda: self.meshChanged.emit("rm"))

    def path(self, which):
        return (self.gt_field if which == "gt" else self.rm_field).text()


class PipelinesPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Pipelines", parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setSpacing(7)
        self.geometry_check = QCheckBox("Geometric (Chamfer, Hausdorff, RMSE, heatmap)")
        self.perceptual_check = QCheckBox("Perceptual (LPIPS, PSNR, SSIM over multiple views)")
        self.geometry_check.setChecked(True)
        self.perceptual_check.setChecked(True)
        layout.addWidget(self.geometry_check)
        layout.addWidget(self.perceptual_check)


def _spin(minimum, maximum, value, decimals=None, step=None, suffix=""):
    box = QDoubleSpinBox() if decimals is not None else QSpinBox()
    if decimals is not None:
        box.setDecimals(decimals)
    box.setRange(minimum, maximum)
    box.setValue(value)
    if step is not None:
        box.setSingleStep(step)
    if suffix:
        box.setSuffix(suffix)
    return box


class ParametersPanel(QGroupBox):
    """Analysis parameters, shown as fixed values (the defaults of ``RunConfig``, i.e. the original pipeline's)."""

    def __init__(self, parent=None):
        super().__init__("Parameters", parent)
        self.setObjectName("card")
        defaults = RunConfig()
        self.mse = QLineEdit(repr(defaults.mse_threshold))
        self.azimuth = _spin(-360, 360, defaults.azimuth, decimals=3, suffix=" °")
        self.elevation = _spin(-90, 90, defaults.elevation, decimals=3, suffix=" °")
        self.width = _spin(64, 8192, defaults.width, suffix=" px")
        self.height = _spin(64, 8192, defaults.height, suffix=" px")
        self.num_views = _spin(1, 1000, defaults.num_views)
        self.margin = _spin(0.5, 3.0, defaults.camera_margin, decimals=3, step=0.01)
        self.radius = _spin(0.5, 10.0, defaults.radius_factor, decimals=3, step=0.05)

        rows = (
            ("ICP threshold", self.mse, "MSE threshold used to decide whether ICP alignment runs."),
            ("Azimuth", self.azimuth, "Geometric render camera azimuth."),
            ("Elevation", self.elevation, "Geometric render camera elevation."),
            ("Views", self.num_views, "Number of views used for perceptual evaluation."),
            ("Width", self.width, "Perceptual render width."),
            ("Height", self.height, "Perceptual render height."),
            ("Camera margin", self.margin, "Camera framing margin."),
            ("Radius factor", self.radius, "Camera radius factor."),
        )
        grid = QGridLayout(self)
        grid.setContentsMargins(10, 8, 10, 8)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)
        for index, (caption, control, tooltip) in enumerate(rows):
            row, pair = divmod(index, 2)
            self._make_read_only(control)
            label = QLabel(caption)
            label.setObjectName("parameterLabel")
            label.setToolTip(tooltip)
            value = QLabel(control.text())
            value.setObjectName("parameterValue")
            value.setToolTip(tooltip)
            control.hide()
            grid.addWidget(label, row, pair * 2)
            grid.addWidget(control, row, pair * 2 + 1)
            grid.addWidget(value, row, pair * 2 + 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

    @staticmethod
    def _make_read_only(control):
        control.setReadOnly(True)
        if isinstance(control, QSpinBox | QDoubleSpinBox):
            control.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        control.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def values(self):
        """``RunConfig`` fields held by this panel."""
        try:
            mse = float(self.mse.text())
        except ValueError:
            mse = float("nan")
        return dict(
            mse_threshold=mse, azimuth=self.azimuth.value(), elevation=self.elevation.value(),
            width=self.width.value(), height=self.height.value(), num_views=self.num_views.value(),
            camera_margin=self.margin.value(), radius_factor=self.radius.value(),
        )


class DevicePanel(QGroupBox):
    """LPIPS device choice plus a background check of the GPU / PyTorch installation."""

    message = Signal(str)  # short status text for the window's status bar

    def __init__(self, parent=None):
        super().__init__("Compute device (LPIPS)", parent)
        self.setObjectName("card")
        self.info = None
        self._process = None

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        self.combo = QComboBox()
        self.combo.addItem("Auto — prefer CUDA", "auto")
        self.combo.addItem("CUDA only", "cuda")
        self.combo.addItem("CPU only", "cpu")
        self.label = QLabel("Detecting…")
        self.label.setWordWrap(True)
        self.warning = QLabel()
        self.warning.setObjectName("warning")
        self.warning.setWordWrap(True)
        self.warning.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.warning.hide()
        self.copy_button = QPushButton("Copy CUDA install command")
        self.copy_button.clicked.connect(self._copy_install_command)
        self.copy_button.hide()
        for widget in (self.combo, self.label, self.warning, self.copy_button):
            layout.addWidget(widget)

    def device(self):
        return self.combo.currentData()

    def detect(self):
        process = QProcess(self)
        process.finished.connect(self._on_detected)
        self._process = process
        process.start(sys.executable, ["-m", "meshcomparison.common.device"])

    def _on_detected(self, _exit_code, _status):
        out = bytes(self._process.readAllStandardOutput()).decode("utf-8", errors="replace").strip()
        self._process = None
        try:
            info = DeviceInfo(**json.loads(out.splitlines()[-1]))
        except (ValueError, TypeError, IndexError):
            self.label.setText("Could not detect the compute device.")
            return
        self.info = info
        self.label.setText(f"Detected: {info.describe()}" + (
            f" · PyTorch {info.torch_version} (CUDA {info.torch_cuda_version})" if info.torch_version else ""))
        if info.warning:
            self.warning.setText(info.warning)
            self.warning.show()
        else:
            self.warning.hide()
        cpu_only_torch = info.nvidia_gpu_detected and info.torch_version and info.torch_cuda_version is None
        self.copy_button.setVisible(bool(cpu_only_torch))

    def _copy_install_command(self):
        QApplication.clipboard().setText(CUDA_INSTALL_COMMAND)
        self.message.emit("CUDA install command copied to the clipboard.")
