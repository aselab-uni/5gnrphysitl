from __future__ import annotations

from PyQt5.QtWidgets import (
    QGroupBox,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class DashboardPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(250)
        self.setMaximumWidth(320)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.status_table = QTableWidget(0, 2)
        self.status_table.setHorizontalHeaderLabels(["Status", "Value"])
        self.status_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.status_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.status_table.setWordWrap(True)
        self.kpi_table = QTableWidget(0, 2)
        self.kpi_table.setHorizontalHeaderLabels(["KPI", "Value"])
        self.kpi_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.kpi_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.note_view = QPlainTextEdit()
        self.note_view.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        status_group = QGroupBox("Environment Status")
        status_layout = QVBoxLayout(status_group)
        status_layout.addWidget(QLabel("Runtime environment details for optional GUI features."))
        status_layout.addWidget(self.status_table)

        kpi_group = QGroupBox("KPI")
        kpi_layout = QVBoxLayout(kpi_group)
        kpi_layout.addWidget(self.kpi_table)

        notes_group = QGroupBox("Warnings / Assumptions")
        notes_layout = QVBoxLayout(notes_group)
        notes_layout.addWidget(QLabel("Runtime notes for simplified models and environment constraints."))
        notes_layout.addWidget(self.note_view)

        log_group = QGroupBox("Logs")
        log_layout = QVBoxLayout(log_group)
        log_layout.addWidget(self.log_view)

        layout.addWidget(status_group, stretch=2)
        layout.addWidget(kpi_group, stretch=2)
        layout.addWidget(notes_group, stretch=2)
        layout.addWidget(log_group, stretch=3)

    def update_kpis(self, kpis: dict) -> None:
        self.kpi_table.setRowCount(len(kpis))
        for row, (key, value) in enumerate(kpis.items()):
            self.kpi_table.setItem(row, 0, QTableWidgetItem(str(key)))
            self.kpi_table.setItem(row, 1, QTableWidgetItem(f"{value:.6g}" if isinstance(value, (int, float)) else str(value)))

    def append_log(self, message: str) -> None:
        self.log_view.appendPlainText(message)

    def set_notes(self, notes: list[str]) -> None:
        self.note_view.setPlainText("\n".join(notes))

    def update_status(self, status_items: dict[str, object]) -> None:
        self.status_table.setRowCount(len(status_items))
        for row, (key, value) in enumerate(status_items.items()):
            self.status_table.setItem(row, 0, QTableWidgetItem(str(key)))
            self.status_table.setItem(row, 1, QTableWidgetItem(str(value)))
