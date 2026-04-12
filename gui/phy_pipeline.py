from __future__ import annotations

from typing import Any

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtWidgets import (
    QLabel,
    QPlainTextEdit,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


pg.setConfigOptions(antialias=True, imageAxisOrder="row-major")


class PhyPipelinePanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.pipeline: list[dict[str, Any]] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.overview_label = QLabel()
        self.overview_label.setWordWrap(True)
        self.overview_label.setTextFormat(Qt.RichText)
        self.overview_label.setText(
            "<b>PHY Pipeline</b><br>"
            "<span style='color:#38bdf8'><b>TX</b></span>: Traffic -> CRC/Coding -> Scrambling -> Modulation -> Grid -> DMRS -> OFDM"
            "<br>"
            "<span style='color:#f59e0b'><b>Channel</b></span>: Impairments -> Fading/Path Loss/Doppler -> AWGN"
            "<br>"
            "<span style='color:#34d399'><b>RX</b></span>: Synchronization -> OFDM Demod -> Channel Estimation -> Equalization -> Soft Demap -> Descrambling -> Decode/CRC"
        )
        layout.addWidget(self.overview_label)

        self.splitter = QSplitter()
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(8)
        layout.addWidget(self.splitter, stretch=1)

        self.stage_tree = QTreeWidget()
        self.stage_tree.setHeaderLabels(["Section", "Stage", "Domain"])
        self.stage_tree.setMinimumWidth(300)
        self.stage_tree.setMaximumWidth(420)
        self.stage_tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.splitter.addWidget(self.stage_tree)

        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(6)

        self.stage_title = QLabel("Select a PHY stage")
        self.stage_title.setWordWrap(True)
        self.stage_title.setTextFormat(Qt.RichText)
        details_layout.addWidget(self.stage_title)

        self.stage_summary = QPlainTextEdit()
        self.stage_summary.setReadOnly(True)
        self.stage_summary.setMaximumBlockCount(200)
        details_layout.addWidget(self.stage_summary, stretch=0)

        self.preview_graphics = pg.GraphicsLayoutWidget()
        self.preview_plot = self.preview_graphics.addPlot(title="Stage Preview")
        self.preview_plot.showGrid(x=True, y=True, alpha=0.25)
        self.preview_plot.getAxis("left").setTextPen("#94a3b8")
        self.preview_plot.getAxis("bottom").setTextPen("#94a3b8")
        self.preview_plot.getAxis("left").setPen(pg.mkPen("#475569"))
        self.preview_plot.getAxis("bottom").setPen(pg.mkPen("#475569"))
        self.preview_image = pg.ImageItem(axisOrder="row-major")
        details_layout.addWidget(self.preview_graphics, stretch=2)

        self.data_excerpt = QPlainTextEdit()
        self.data_excerpt.setReadOnly(True)
        self.data_excerpt.setMaximumBlockCount(400)
        details_layout.addWidget(self.data_excerpt, stretch=1)

        self.splitter.addWidget(details_widget)
        self.splitter.setSizes([340, 900])

    def set_pipeline(self, pipeline: list[dict[str, Any]]) -> None:
        self.pipeline = pipeline
        self.stage_tree.clear()
        groups: dict[str, QTreeWidgetItem] = {}

        for index, stage in enumerate(self.pipeline):
            section = str(stage.get("section", "Other"))
            if section not in groups:
                group = QTreeWidgetItem([section, "", ""])
                group.setFirstColumnSpanned(True)
                groups[section] = group
                self.stage_tree.addTopLevelItem(group)
            item = QTreeWidgetItem(
                [
                    section,
                    str(stage.get("stage", f"Stage {index + 1}")),
                    str(stage.get("domain", "")),
                ]
            )
            item.setData(0, Qt.UserRole, index)
            groups[section].addChild(item)

        for section_item in groups.values():
            section_item.setExpanded(True)

        if self.pipeline:
            first_group = self.stage_tree.topLevelItem(0)
            if first_group and first_group.childCount() > 0:
                self.stage_tree.setCurrentItem(first_group.child(0))

    def _on_selection_changed(self) -> None:
        items = self.stage_tree.selectedItems()
        if not items:
            return
        item = items[0]
        index = item.data(0, Qt.UserRole)
        if index is None:
            return
        stage = self.pipeline[int(index)]
        self._render_stage(stage)

    @staticmethod
    def _format_excerpt(data: Any, max_entries: int = 48) -> str:
        array = np.asarray(data)
        if array.ndim == 0:
            return str(array.item())
        flat = array.reshape(-1)
        clipped = flat[:max_entries]
        if np.issubdtype(clipped.dtype, np.integer):
            body = " ".join(str(int(value)) for value in clipped)
        elif np.issubdtype(clipped.dtype, np.floating):
            body = " ".join(f"{float(value):.4g}" for value in clipped)
        elif np.issubdtype(clipped.dtype, np.complexfloating):
            body = " ".join(f"{value.real:.4g}{value.imag:+.4g}j" for value in clipped)
        else:
            body = " ".join(str(value) for value in clipped)
        if flat.size > max_entries:
            body += " ..."
        return body

    @staticmethod
    def _summary_text(stage: dict[str, Any], data: Any) -> str:
        array = np.asarray(data)
        summary = [
            f"Section: {stage.get('section', 'n/a')}",
            f"Stage: {stage.get('stage', 'n/a')}",
            f"Domain: {stage.get('domain', 'n/a')}",
            f"Preview kind: {stage.get('preview_kind', 'n/a')}",
            f"Shape: {array.shape}",
            f"Dtype: {array.dtype}",
            "",
            str(stage.get("description", "")),
        ]
        if array.size:
            if np.iscomplexobj(array):
                magnitudes = np.abs(array)
                summary.extend(
                    [
                        "",
                        f"Mean |x|: {float(np.mean(magnitudes)):.4g}",
                        f"Peak |x|: {float(np.max(magnitudes)):.4g}",
                    ]
                )
            elif np.issubdtype(array.dtype, np.number):
                summary.extend(
                    [
                        "",
                        f"Min: {float(np.min(array)):.4g}",
                        f"Max: {float(np.max(array)):.4g}",
                        f"Mean: {float(np.mean(array)):.4g}",
                    ]
                )
        return "\n".join(summary)

    def _render_stage(self, stage: dict[str, Any]) -> None:
        data = stage.get("data", np.array([]))
        preview_kind = str(stage.get("preview_kind", "text"))
        array = np.asarray(data)

        self.stage_title.setText(
            f"<b>{stage.get('section', 'Other')}</b>  |  <b>{stage.get('stage', 'Stage')}</b>  |  {stage.get('domain', '')}"
        )
        self.stage_summary.setPlainText(self._summary_text(stage, data))
        self.data_excerpt.setPlainText(f"Excerpt:\n{self._format_excerpt(data)}")
        self._render_preview(preview_kind, array)

    def _reset_preview(self, title: str) -> None:
        self.preview_plot.clear()
        self.preview_plot.setTitle(title)
        self.preview_plot.showGrid(x=True, y=True, alpha=0.25)
        self.preview_plot.getAxis("left").setTextPen("#94a3b8")
        self.preview_plot.getAxis("bottom").setTextPen("#94a3b8")
        self.preview_plot.getAxis("left").setPen(pg.mkPen("#475569"))
        self.preview_plot.getAxis("bottom").setPen(pg.mkPen("#475569"))

    def _set_image(self, image: np.ndarray) -> None:
        self.preview_plot.addItem(self.preview_image)
        self.preview_image.setImage(image, autoLevels=True)
        self.preview_image.setLookupTable(pg.colormap.get("viridis").getLookupTable())
        height, width = image.shape
        self.preview_image.setRect(QRectF(0.0, 0.0, float(width), float(height)))
        self.preview_plot.setXRange(0.0, float(width), padding=0.0)
        self.preview_plot.setYRange(0.0, float(height), padding=0.0)

    def _render_preview(self, preview_kind: str, array: np.ndarray) -> None:
        self._reset_preview("Stage Preview")
        if array.size == 0:
            self.preview_plot.addItem(pg.TextItem("No data", color="#d8dee9", anchor=(0.5, 0.5)))
            return

        if preview_kind == "bits":
            view = array.reshape(-1)[:256].astype(float)
            x_axis = np.arange(view.size + 1, dtype=float) - 0.5
            self.preview_plot.setLabel("bottom", "Bit index")
            self.preview_plot.setLabel("left", "Bit value")
            self.preview_plot.plot(x_axis, view, pen=pg.mkPen("#38bdf8", width=1.4), stepMode="center")
            self.preview_plot.setYRange(-0.2, 1.2, padding=0.0)
            return

        if preview_kind == "llr":
            view = array.reshape(-1)[:256].astype(float)
            x_axis = np.arange(view.size)
            self.preview_plot.setLabel("bottom", "LLR index")
            self.preview_plot.setLabel("left", "LLR")
            self.preview_plot.plot(x_axis, view, pen=pg.mkPen("#f97316", width=1.4))
            return

        if preview_kind == "waveform":
            view = array.reshape(-1)[:2048]
            x_axis = np.arange(view.size)
            self.preview_plot.addLegend(offset=(10, 10))
            self.preview_plot.setLabel("bottom", "Sample")
            self.preview_plot.setLabel("left", "Amplitude")
            self.preview_plot.plot(x_axis, view.real, pen=pg.mkPen("#60a5fa", width=1.2), name="I")
            self.preview_plot.plot(x_axis, view.imag, pen=pg.mkPen("#f59e0b", width=1.2), name="Q")
            return

        if preview_kind == "constellation":
            view = array.reshape(-1)[:1024]
            self.preview_plot.setLabel("bottom", "In-Phase")
            self.preview_plot.setLabel("left", "Quadrature")
            self.preview_plot.setAspectLocked(True)
            scatter = pg.ScatterPlotItem(
                x=view.real,
                y=view.imag,
                pen=pg.mkPen("#0ea5e9", width=0.8),
                brush=pg.mkBrush(56, 189, 248, 120),
                size=6,
            )
            self.preview_plot.addItem(scatter)
            return

        if preview_kind == "grid":
            image = np.abs(array).astype(np.float32)
            self.preview_plot.setLabel("bottom", "Subcarrier")
            self.preview_plot.setLabel("left", "OFDM symbol")
            self._set_image(image)
            return

        view = array.reshape(-1)[:256].astype(float)
        self.preview_plot.plot(np.arange(view.size), view, pen=pg.mkPen("#cbd5e1", width=1.2))
