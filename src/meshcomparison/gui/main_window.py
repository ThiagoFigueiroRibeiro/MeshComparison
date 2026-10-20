import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton,
    QScrollArea, QSplitter, QTabWidget, QVBoxLayout, QWidget,
)

from ..common.io import load_mesh
from .config import RunConfig, validate
from .outputs import load_run_meshes
from .panels import DevicePanel, MeshesPanel, ParametersPanel, PipelinesPanel
from .results_view import ResultsView
from .runner import PipelineRunner
from .viewer3d import MeshViewer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mesh Comparison")
        self.resize(1400, 860)

        self.runner = PipelineRunner(self)
        self.runner.log.connect(self._append_log)
        self.runner.progress.connect(self._on_progress)
        self.runner.finished.connect(self._on_finished)

        self._last_cfg = None

        self.viewer = MeshViewer()
        self.results = ResultsView()
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(5000)
        self.log_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        mono = self.log_view.font()
        mono.setFamily("Consolas" if sys.platform == "win32" else "monospace")
        self.log_view.setFont(mono)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.viewer, "3D view")
        self.tabs.addTab(self.results, "Results")
        self.tabs.addTab(self.log_view, "Log")

        splitter = QSplitter()
        splitter.addWidget(self._build_side_panel())
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([400, 1000])
        splitter.setChildrenCollapsible(False)
        self.setCentralWidget(splitter)

        self.statusBar().showMessage("Ready")
        self.device_panel.detect()

    # ---- construction -------------------------------------------------

    def _build_side_panel(self):
        panel = QWidget()
        panel.setObjectName("sidePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        heading = QLabel("Evaluate meshes")
        heading.setObjectName("panelHeading")
        subtitle = QLabel("Compare geometry and visual similarity")
        subtitle.setObjectName("panelSubtitle")
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        self.meshes_panel = MeshesPanel()
        self.meshes_panel.meshChanged.connect(self._preview)
        self.pipelines_panel = PipelinesPanel()
        self.parameters_panel = ParametersPanel()
        self.device_panel = DevicePanel()
        self.device_panel.message.connect(lambda text: self.statusBar().showMessage(text, 5000))
        for card in (self.meshes_panel, self.pipelines_panel, self.parameters_panel, self.device_panel):
            layout.addWidget(card)

        self.run_button = QPushButton("Run evaluation")
        self.run_button.setObjectName("primary")
        self.run_button.clicked.connect(self._run)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.runner.cancel)
        buttons = QHBoxLayout()
        buttons.addWidget(self.run_button, 1)
        buttons.addWidget(self.cancel_button)
        layout.addLayout(buttons)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress_label = QLabel("")
        self.progress_label.setObjectName("hint")
        self.progress_label.setWordWrap(True)
        layout.addWidget(self.progress)
        layout.addWidget(self.progress_label)
        layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(panel)
        scroll.setMinimumWidth(380)
        return scroll

    # ---- actions ------------------------------------------------------

    def _config(self):
        return RunConfig(
            gt=self.meshes_panel.path("gt"), rm=self.meshes_panel.path("rm"),
            out=self.meshes_panel.out_field.text(),
            run_geometry=self.pipelines_panel.geometry_check.isChecked(),
            run_perceptual=self.pipelines_panel.perceptual_check.isChecked(),
            device=self.device_panel.device(),
            **self.parameters_panel.values(),
        )

    def _preview(self, which):
        path = self.meshes_panel.path(which)
        if not path or not os.path.isfile(path) or path.lower().endswith(".fbx"):
            self.viewer.set_layer(which, None)
            return
        try:
            QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
            self.viewer.set_layer(which, load_mesh(path))
            self.tabs.setCurrentWidget(self.viewer)
        except Exception as exc:
            QMessageBox.warning(self, "Could not load mesh", str(exc))
        finally:
            QApplication.restoreOverrideCursor()

    def _run(self):
        cfg = self._config()
        errors = validate(cfg)
        if cfg.mse_threshold != cfg.mse_threshold:  # NaN
            errors.append("MSE threshold is not a valid number.")
        if errors:
            QMessageBox.warning(self, "Cannot run", "\n".join(errors))
            return
        os.makedirs(cfg.out, exist_ok=True)
        self._last_cfg = cfg
        self.log_view.clear()
        self.tabs.setCurrentWidget(self.log_view)
        self._set_running(True)
        self.runner.start(cfg)

    def _set_running(self, running):
        self.run_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        if running:
            self.progress.setValue(0)

    def _append_log(self, text):
        self.log_view.appendPlainText(text)

    def _on_progress(self, percent, label):
        self.progress.setValue(percent)
        self.progress_label.setText(label)

    def _on_finished(self, success, message):
        self._set_running(False)
        self.statusBar().showMessage(message, 8000)
        self.progress_label.setText(message)
        self._append_log(f"\n{message}")
        if not success:
            if "cancelled" not in message:
                QMessageBox.critical(self, "Evaluation failed", message)
            return
        cfg = self._last_cfg
        self.results.load(cfg.out)
        self._show_result_3d(cfg)
        self.tabs.setCurrentWidget(self.viewer)

    def _show_result_3d(self, cfg):
        try:
            meshes = load_run_meshes(cfg.gt, cfg.out, with_heatmap=cfg.run_geometry)
            self.viewer.show_run_result(
                meshes.gt, meshes.rm_aligned, meshes.heatmap, meshes.heatmap_scale, meshes.heatmap_vmax)
        except Exception as exc:
            self._append_log(f"Could not display the 3D result: {exc}")

    def closeEvent(self, event):
        if self.runner.running:
            self.runner.cancel()
        self.viewer.close_plotter()
        super().closeEvent(event)
