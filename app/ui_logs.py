from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class LogsPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db

        layout = QVBoxLayout(self)

        self.refresh_button = QPushButton("Refresh Logs")
        self.refresh_button.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_button)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Mode", "Action", "Chemical", "CAS", "Details", "User"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        rows = self.db.list_logs()
        self.table.clearContents()
        self.table.setRowCount(len(rows))

        fields = ["timestamp", "mode", "action", "chemical_name", "cas", "details", "user"]
        for i, row in enumerate(rows):
            for j, field in enumerate(fields):
                value = row[field] if row[field] is not None else ""
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, j, item)

        self.table.resizeColumnsToContents()
