from __future__ import annotations

from PyQt5.QtWidgets import QHeaderView, QPlainTextEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class DashboardPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.kpi_table = QTableWidget(0, 2)
        self.kpi_table.setHorizontalHeaderLabels(["KPI", "Value"])
        self.kpi_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.kpi_table, stretch=2)
        layout.addWidget(self.log_view, stretch=3)

    def update_kpis(self, kpis: dict) -> None:
        self.kpi_table.setRowCount(len(kpis))
        for row, (key, value) in enumerate(kpis.items()):
            self.kpi_table.setItem(row, 0, QTableWidgetItem(str(key)))
            self.kpi_table.setItem(row, 1, QTableWidgetItem(f"{value:.6g}" if isinstance(value, (int, float)) else str(value)))

    def append_log(self, message: str) -> None:
        self.log_view.appendPlainText(message)
