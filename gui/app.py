from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QMessageBox, QSplitter, QWidget

from experiments.ber_vs_snr import run_experiment as run_ber_vs_snr
from experiments.common import simulate_link
from gui.config_editor import load_config_dialog, save_config_dialog
from gui.controls import ControlPanel
from gui.dashboard import DashboardPanel
from gui.plots import PlotPanel
from utils.validators import deep_merge


class SimulationWorker(QObject):
    finished = pyqtSignal()
    result_ready = pyqtSignal(object)
    log_message = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, config: dict, batch: bool = False) -> None:
        super().__init__()
        self.config = config
        self.batch = batch

    def run(self) -> None:
        try:
            if self.batch:
                self.log_message.emit("Running batch BER vs SNR experiment.")
                output_dir = Path(self.config.get("simulation", {}).get("output_dir", "outputs"))
                dataframe = run_ber_vs_snr(self.config, output_dir=output_dir)
                self.result_ready.emit({"dataframe": dataframe})
            else:
                self.log_message.emit("Running single-link simulation.")
                result = simulate_link(self.config)
                self.result_ready.emit(result)
        except Exception as exc:  # pragma: no cover - GUI path
            self.error.emit(str(exc))
        finally:
            self.finished.emit()


class NrPhyResearchApp(QMainWindow):
    def __init__(self, base_config: dict) -> None:
        super().__init__()
        self.setWindowTitle("5G NR PHY STL Research Dashboard")
        self.resize(1600, 900)
        self.base_config = deepcopy(base_config)
        self.current_config = deepcopy(base_config)
        self.thread: QThread | None = None
        self.worker: SimulationWorker | None = None

        self.controls = ControlPanel()
        self.controls.apply_config(self.current_config)
        self.plots = PlotPanel()
        self.dashboard = DashboardPanel()

        self._build_ui()
        self._connect_signals()
        self.dashboard.append_log("Dashboard initialized.")

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QHBoxLayout(central)
        splitter = QSplitter()
        splitter.addWidget(self.controls)
        splitter.addWidget(self.plots)
        splitter.addWidget(self.dashboard)
        splitter.setSizes([320, 800, 400])
        layout.addWidget(splitter)
        self.setCentralWidget(central)

    def _connect_signals(self) -> None:
        self.controls.buttons["run"].clicked.connect(self.run_single)
        self.controls.buttons["batch"].clicked.connect(self.run_batch)
        self.controls.buttons["reset"].clicked.connect(self.reset_config)
        self.controls.buttons["save"].clicked.connect(self.save_config)
        self.controls.buttons["load"].clicked.connect(self.load_config)
        self.controls.buttons["stop"].clicked.connect(self.stop_worker)

    def _build_runtime_config(self) -> dict:
        self.current_config = deep_merge(self.base_config, self.controls.build_patch())
        return deepcopy(self.current_config)

    def _start_worker(self, config: dict, batch: bool) -> None:
        if self.thread is not None:
            self.dashboard.append_log("Worker already running.")
            return
        self.thread = QThread()
        self.worker = SimulationWorker(config=config, batch=batch)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.log_message.connect(self.dashboard.append_log)
        self.worker.result_ready.connect(self.handle_result)
        self.worker.error.connect(self.handle_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._clear_worker)
        self.thread.start()

    def _clear_worker(self) -> None:
        self.thread = None
        self.worker = None
        self.dashboard.append_log("Worker finished.")

    def run_single(self) -> None:
        config = self._build_runtime_config()
        self.dashboard.append_log("Preparing single-link run.")
        self._start_worker(config=config, batch=False)

    def run_batch(self) -> None:
        config = self._build_runtime_config()
        self.dashboard.append_log("Preparing batch experiment.")
        self._start_worker(config=config, batch=True)

    def stop_worker(self) -> None:
        if self.thread is None:
            self.dashboard.append_log("No worker is active.")
            return
        self.thread.requestInterruption()
        self.dashboard.append_log("Stop requested. The current batch will end at the next safe point.")

    def reset_config(self) -> None:
        self.current_config = deepcopy(self.base_config)
        self.controls.apply_config(self.current_config)
        self.dashboard.append_log("Configuration reset to defaults.")

    def save_config(self) -> None:
        config = self._build_runtime_config()
        path = save_config_dialog(self, config)
        if path:
            self.dashboard.append_log(f"Configuration saved to {path}")

    def load_config(self) -> None:
        config = load_config_dialog(self)
        if config is None:
            return
        self.current_config = deep_merge(self.base_config, config)
        self.controls.apply_config(self.current_config)
        self.dashboard.append_log("Configuration loaded from YAML.")

    def handle_result(self, result: object) -> None:
        if isinstance(result, dict) and "tx" in result:
            self.plots.update_from_result(result)
            self.dashboard.update_kpis(result["kpis"].as_dict())
            self.dashboard.append_log("Single-link simulation completed.")
        elif isinstance(result, dict) and "dataframe" in result:
            dataframe = result["dataframe"]
            self.dashboard.append_log(f"Batch experiment completed with {len(dataframe)} points.")
            self.dashboard.update_kpis({"rows": len(dataframe), "min_ber": float(dataframe['ber'].min()), "max_ber": float(dataframe['ber'].max())})

    def handle_error(self, message: str) -> None:
        self.dashboard.append_log(f"Error: {message}")
        QMessageBox.critical(self, "Simulation error", message)


def launch_app(config: dict) -> None:
    app = QApplication.instance() or QApplication([])
    window = NrPhyResearchApp(config)
    window.show()
    app.exec_()
