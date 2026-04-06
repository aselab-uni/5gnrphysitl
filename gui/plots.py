from __future__ import annotations

from typing import Dict

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QWidget


class PlotPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.figure = Figure(figsize=(12, 8), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.axes = self.figure.subplots(3, 2)
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

    def update_from_result(self, result: Dict) -> None:
        tx = result["tx"]
        rx = result["rx"]
        rx_waveform = result["rx_waveform"]
        channel_state = result["channel_state"]

        constellation_axis = self.axes[0, 0]
        waveform_axis = self.axes[0, 1]
        spectrum_axis = self.axes[1, 0]
        impulse_axis = self.axes[1, 1]
        channel_axis = self.axes[2, 0]
        trend_axis = self.axes[2, 1]

        for axis in self.axes.ravel():
            axis.clear()
            axis.grid(True, alpha=0.2)

        constellation_axis.scatter(rx.equalized_symbols.real, rx.equalized_symbols.imag, s=8, alpha=0.7)
        constellation_axis.set_title("Equalized Constellation")
        constellation_axis.set_xlabel("I")
        constellation_axis.set_ylabel("Q")

        waveform_axis.plot(np.real(rx_waveform[:2048]), label="I")
        waveform_axis.plot(np.imag(rx_waveform[:2048]), label="Q", alpha=0.7)
        waveform_axis.set_title("Received Waveform")
        waveform_axis.legend(loc="upper right")

        spectrum = np.fft.fftshift(np.fft.fft(rx_waveform[:4096], n=4096))
        freqs = np.linspace(-tx.metadata.sample_rate / 2, tx.metadata.sample_rate / 2, spectrum.size)
        spectrum_axis.plot(freqs / 1e6, 20 * np.log10(np.abs(spectrum) + 1e-9))
        spectrum_axis.set_title("Spectrum")
        spectrum_axis.set_xlabel("Frequency (MHz)")
        spectrum_axis.set_ylabel("Magnitude (dB)")

        impulse = channel_state.get("impulse_response", np.array([1.0 + 0j]))
        impulse_axis.stem(np.arange(len(impulse)), np.abs(impulse), basefmt=" ")
        impulse_axis.set_title("Channel Impulse Response")
        impulse_axis.set_xlabel("Tap")

        channel_axis.imshow(np.abs(rx.channel_estimate), aspect="auto", origin="lower", cmap="viridis")
        channel_axis.set_title("Estimated Channel Magnitude")
        channel_axis.set_xlabel("Subcarrier")
        channel_axis.set_ylabel("OFDM Symbol")

        kpis = rx.kpis.as_dict()
        trend_axis.bar(list(kpis.keys())[:6], list(kpis.values())[:6], color="#1f77b4")
        trend_axis.set_title("KPI Snapshot")
        trend_axis.tick_params(axis="x", rotation=30)

        self.canvas.draw_idle()
