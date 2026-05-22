from PySide6.QtWidgets import QAbstractItemView, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class LogsPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        refresh_btn = QPushButton("Refresh Logs")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Mode", "Action", "Chemical", "CAS", "Details", "User"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

    def refresh(self):
        rows = self.db.list_logs()
        self.table.setSortingEnabled(False)
        self.table.clearContents()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [r["timestamp"], r["mode"], r["action"], r["chemical_name"], r["cas"], r["details"], r["user"]]
            for j, v in enumerate(vals):
                self.table.setItem(i, j, QTableWidgetItem("" if v is None else str(v)))
        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(True)
