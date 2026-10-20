"""Runs the evaluation pipelines in child processes so rendering (pyrender/OpenGL) never shares a context
with the 3D viewer and a run can be cancelled cleanly."""
from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, Signal

from .config import ProgressTracker, build_commands


class PipelineRunner(QObject):
    log = Signal(str)
    progress = Signal(int, str)  # percent, label
    finished = Signal(bool, str)  # success, message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process = None
        self._queue = []
        self._python = None
        self._tracker = None
        self._buffer = ""
        self._cancelled = False
        self._current = ""

    @property
    def running(self):
        return self._process is not None

    def start(self, cfg):
        if self.running:
            return
        self._python, self._queue = build_commands(cfg)
        self._tracker = ProgressTracker(len(self._queue))
        self._cancelled = False
        self._index = 0
        self._launch_next()

    def cancel(self):
        if self._process is None:
            return
        self._cancelled = True
        self._queue.clear()
        self._process.kill()

    def _launch_next(self):
        command = self._queue.pop(0)
        self._current = command.name
        self._tracker.start_command(self._index)
        self._buffer = ""

        process = QProcess(self)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONUNBUFFERED", "1")
        env.insert("PYTHONIOENCODING", "utf-8")
        process.setProcessEnvironment(env)
        process.readyReadStandardOutput.connect(self._on_output)
        process.finished.connect(self._on_finished)
        process.errorOccurred.connect(self._on_error)
        self._process = process

        self.log.emit(f"\n=== {command.name} pipeline ===")
        self.progress.emit(int(self._tracker.fraction * 100), f"{command.name}: starting")
        process.start(self._python, command.args)
        if command.stdin:
            process.write(command.stdin.encode("utf-8"))
        process.closeWriteChannel()

    def _on_output(self):
        data = bytes(self._process.readAllStandardOutput()).decode("utf-8", errors="replace")
        self._buffer += data.replace("\r\n", "\n").replace("\r", "\n")
        *lines, self._buffer = self._buffer.split("\n")
        for line in lines:
            self.log.emit(line)
            self._tracker.feed(line)
        if lines:
            self.progress.emit(int(self._tracker.fraction * 100), f"{self._current}: {lines[-1].strip()[:80]}")

    def _on_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.log.emit(f"Could not start Python process: {self._process.errorString()}")

    def _on_finished(self, exit_code, _status):
        if self._buffer.strip():
            self.log.emit(self._buffer)
            self._tracker.feed(self._buffer)
        process, self._process = self._process, None
        process.deleteLater()

        if self._cancelled:
            self.finished.emit(False, "Run cancelled.")
            return
        if exit_code != 0:
            self._queue.clear()
            self.finished.emit(False, f"{self._current} pipeline failed (exit code {exit_code}). See the log.")
            return

        self._tracker.finish_command()
        self._index += 1
        if self._queue:
            self._launch_next()
        else:
            self.progress.emit(100, "Done")
            self.finished.emit(True, "Evaluation finished.")
