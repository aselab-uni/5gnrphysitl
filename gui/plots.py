from __future__ import annotations

from typing import Dict

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import QRectF
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QWidget


pg.setConfigOptions(antialias=True, imageAxisOrder="row-major")


class PlotPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.graphics = pg.GraphicsLayoutWidget()
        self.graphics.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(self)
        layout.addWidget(self.graphics)
        self._build_workspace()

    def _build_workspace(self) -> None:
        title_style = {"color": "#d8dee9", "size": "11pt"}

        self.constellation_plot = self.graphics.addPlot(row=0, col=0, title="Constellation: pre/post/reference")
        self.constellation_plot.showGrid(x=True, y=True, alpha=0.25)
        self.constellation_plot.setLabel("bottom", "In-Phase")
        self.constellation_plot.setLabel("left", "Quadrature")
        self.constellation_plot.setAspectLocked(True)
        self.constellation_plot.addLegend(offset=(10, 10))
        self.reference_scatter = self.constellation_plot.plot(
            pen=None,
            symbol="x",
            symbolPen=pg.mkPen("#f94144", width=1.2),
            symbolSize=7,
            name="Reference",
        )
        self.pre_eq_scatter = self.constellation_plot.plot(
            pen=None,
            symbol="o",
            symbolBrush=pg.mkBrush(255, 255, 255, 50),
            symbolPen=pg.mkPen(255, 255, 255, 80),
            symbolSize=4,
            name="Pre-EQ",
        )
        self.post_eq_scatter = self.constellation_plot.plot(
            pen=None,
            symbol="o",
            symbolBrush=pg.mkBrush("#38bdf8"),
            symbolPen=pg.mkPen("#0ea5e9", width=0.8),
            symbolSize=5,
            name="Post-EQ",
        )

        self.waveform_plot = self.graphics.addPlot(row=0, col=1, title="RX waveform (time domain)")
        self.waveform_plot.showGrid(x=True, y=True, alpha=0.25)
        self.waveform_plot.setLabel("bottom", "Sample")
        self.waveform_plot.setLabel("left", "Amplitude")
        self.waveform_i_curve = self.waveform_plot.plot(pen=pg.mkPen("#60a5fa", width=1.3), name="I")
        self.waveform_q_curve = self.waveform_plot.plot(pen=pg.mkPen("#f59e0b", width=1.3), name="Q")

        self.spectrum_plot = self.graphics.addPlot(row=1, col=0, title="RX spectrum")
        self.spectrum_plot.showGrid(x=True, y=True, alpha=0.25)
        self.spectrum_plot.setLabel("bottom", "Frequency (MHz)")
        self.spectrum_plot.setLabel("left", "Magnitude (dB)")
        self.spectrum_curve = self.spectrum_plot.plot(pen=pg.mkPen("#34d399", width=1.4))

        self.resource_plot = self.graphics.addPlot(row=1, col=1, title="TX resource-grid allocation")
        self.resource_plot.showGrid(x=True, y=True, alpha=0.15)
        self.resource_plot.setLabel("bottom", "Subcarrier")
        self.resource_plot.setLabel("left", "OFDM symbol")
        self.resource_image = pg.ImageItem(axisOrder="row-major")
        self.resource_plot.addItem(self.resource_image)
        resource_lut = np.array(
            [
                [15, 23, 42, 255],
                [56, 189, 248, 255],
                [251, 191, 36, 255],
            ],
            dtype=np.ubyte,
        )
        self.resource_image.setLookupTable(resource_lut)
        self.resource_image.setLevels((0, 2))

        self.channel_plot = self.graphics.addPlot(row=2, col=0, title="Estimated channel magnitude")
        self.channel_plot.showGrid(x=True, y=True, alpha=0.15)
        self.channel_plot.setLabel("bottom", "Subcarrier")
        self.channel_plot.setLabel("left", "OFDM symbol")
        self.channel_image = pg.ImageItem(axisOrder="row-major")
        self.channel_plot.addItem(self.channel_image)
        channel_cmap = pg.colormap.get("viridis")
        self.channel_image.setLookupTable(channel_cmap.getLookupTable())

        self.impulse_plot = self.graphics.addPlot(row=2, col=1, title="Channel impulse response")
        self.impulse_plot.showGrid(x=True, y=True, alpha=0.25)
        self.impulse_plot.setLabel("bottom", "Tap")
        self.impulse_plot.setLabel("left", "Magnitude")
        self.impulse_stem = self.impulse_plot.plot(
            pen=pg.mkPen("#a78bfa", width=1.2),
            symbol="o",
            symbolBrush=pg.mkBrush("#c4b5fd"),
            symbolPen=pg.mkPen("#8b5cf6", width=0.8),
            symbolSize=6,
        )

        for item in [
            self.constellation_plot,
            self.waveform_plot,
            self.spectrum_plot,
            self.resource_plot,
            self.channel_plot,
            self.impulse_plot,
        ]:
            item.getAxis("left").setTextPen("#94a3b8")
            item.getAxis("bottom").setTextPen("#94a3b8")
            item.getAxis("left").setPen(pg.mkPen("#475569"))
            item.getAxis("bottom").setPen(pg.mkPen("#475569"))
            item.titleLabel.item.setDefaultTextColor(pg.mkColor(title_style["color"]))

    @staticmethod
    def _resource_allocation_map(result: Dict) -> np.ndarray:
        tx = result["tx"]
        numerology = tx.metadata.numerology
        allocation_map = np.zeros(
            (numerology.symbols_per_slot, numerology.active_subcarriers),
            dtype=np.float32,
        )
        mapping_positions = tx.metadata.mapping.positions
        if mapping_positions.size:
            allocation_map[mapping_positions[:, 0], mapping_positions[:, 1]] = 1.0
        dmrs_positions = tx.metadata.dmrs["positions"]
        if dmrs_positions.size:
            allocation_map[dmrs_positions[:, 0], dmrs_positions[:, 1]] = 2.0
        return allocation_map

    @staticmethod
    def _reference_symbols(result: Dict) -> np.ndarray:
        tx = result["tx"]
        positions = tx.metadata.mapping.positions
        return tx.metadata.tx_grid[positions[:, 0], positions[:, 1]]

    @staticmethod
    def _pre_equalized_symbols(result: Dict) -> np.ndarray:
        tx = result["tx"]
        rx = result["rx"]
        positions = tx.metadata.mapping.positions
        return rx.rx_grid[positions[:, 0], positions[:, 1]]

    @staticmethod
    def _set_image(plot_item: pg.PlotItem, image_item: pg.ImageItem, data: np.ndarray) -> None:
        height, width = data.shape
        image_item.setImage(data, autoLevels=False)
        image_item.setRect(QRectF(0.0, 0.0, float(width), float(height)))
        plot_item.setXRange(0.0, float(width), padding=0.0)
        plot_item.setYRange(0.0, float(height), padding=0.0)

    def update_from_result(self, result: Dict) -> None:
        tx = result["tx"]
        rx = result["rx"]
        rx_waveform = result["rx_waveform"]
        channel_state = result["channel_state"]
        reference_symbols = self._reference_symbols(result)
        pre_equalized_symbols = self._pre_equalized_symbols(result)

        self.reference_scatter.setData(reference_symbols.real, reference_symbols.imag)
        self.pre_eq_scatter.setData(pre_equalized_symbols.real, pre_equalized_symbols.imag)
        self.post_eq_scatter.setData(rx.equalized_symbols.real, rx.equalized_symbols.imag)
        max_symbol = max(
            float(np.max(np.abs(reference_symbols))) if reference_symbols.size else 1.0,
            float(np.max(np.abs(pre_equalized_symbols))) if pre_equalized_symbols.size else 1.0,
            float(np.max(np.abs(rx.equalized_symbols))) if rx.equalized_symbols.size else 1.0,
            1.0,
        )
        self.constellation_plot.setXRange(-1.2 * max_symbol, 1.2 * max_symbol, padding=0.0)
        self.constellation_plot.setYRange(-1.2 * max_symbol, 1.2 * max_symbol, padding=0.0)

        waveform_view = rx_waveform[:2048]
        samples = np.arange(waveform_view.size)
        self.waveform_i_curve.setData(samples, waveform_view.real)
        self.waveform_q_curve.setData(samples, waveform_view.imag)

        spectrum_view = rx_waveform[:4096]
        if spectrum_view.size == 0:
            spectrum = np.zeros(4096, dtype=np.complex128)
        else:
            spectrum = np.fft.fftshift(np.fft.fft(spectrum_view, n=4096))
        freqs = np.linspace(-tx.metadata.sample_rate / 2, tx.metadata.sample_rate / 2, spectrum.size)
        self.spectrum_curve.setData(freqs / 1e6, 20.0 * np.log10(np.abs(spectrum) + 1e-9))

        resource_map = self._resource_allocation_map(result)
        self._set_image(self.resource_plot, self.resource_image, resource_map)

        channel_magnitude = np.abs(rx.channel_estimate).astype(np.float32)
        channel_max = float(np.max(channel_magnitude)) if channel_magnitude.size else 1.0
        self.channel_image.setLevels((0.0, max(channel_max, 1e-6)))
        self._set_image(self.channel_plot, self.channel_image, channel_magnitude)

        impulse = np.asarray(channel_state.get("impulse_response", np.array([1.0 + 0j])), dtype=np.complex128)
        taps = np.arange(impulse.size)
        self.impulse_stem.setData(taps, np.abs(impulse))
