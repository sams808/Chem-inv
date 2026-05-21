import webbrowser
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
                               QMainWindow, QMenuBar, QMessageBox, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from .ghs_tools import parse_ghs_codes
from .import_export import backup_database, export_rows, import_csv
from .sds_tools import build_search_urls, open_local_sds
from .ui_dashboard import DashboardPage
from .ui_forms import ChemicalFormDialog


class NumericTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except (TypeError, ValueError):
            return super().__lt__(other)


class MainWindow(QMainWindow):
    def __init__(self, db, base_dir: Path):
        super().__init__()
        self.db = db
        self.base_dir = base_dir
        self.current_id = None
        self.setWindowTitle("Lab Chemical Inventory Manager")
        self.resize(1280, 800)
        self._menu()
        self._ui()
        self.refresh()

    def _menu(self):
        mb = QMenuBar(self); file_menu = mb.addMenu("File")
        file_menu.addAction("Import CSV", self.import_csv_action)
        file_menu.addAction("Export Inventory CSV", self.export_all)
        file_menu.addAction("Export Active Inventory CSV", self.export_active)
        file_menu.addAction("Export Logs CSV", self.export_logs)
        file_menu.addAction("Backup Database", self.backup_action)
        self.setMenuBar(mb)

    def _ui(self):
        c = QWidget(); self.setCentralWidget(c)
        h = QHBoxLayout(c)
        left = QVBoxLayout(); h.addLayout(left, 1)
        for text, cb in [("Inventory", self.refresh), ("Add Chemical", self.add_chemical), ("Dashboard", self.show_dashboard), ("Logs", None), ("Settings", None)]:
            b = QPushButton(text); left.addWidget(b)
            if cb: b.clicked.connect(cb)
        left.addStretch(1)
        mid = QVBoxLayout(); h.addLayout(mid, 6)
        self.search = QLineEdit(); self.search.setPlaceholderText("search")
        self.search.textChanged.connect(self.refresh); mid.addWidget(self.search)
        self.status_filter = QComboBox(); self.status_filter.addItems(["all","active","empty","disposed","archived","error_duplicate"])
        self.status_filter.currentTextChanged.connect(self.refresh); mid.addWidget(self.status_filter)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Name","CAS","Quantity","Unit","Location","State","GHS","Status"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.itemSelectionChanged.connect(self.select_row)
        mid.addWidget(self.table)
        right = QVBoxLayout(); h.addLayout(right, 3)
        self.details = QLabel("Select chemical")
        self.details.setWordWrap(True); right.addWidget(self.details)
        for text, cb in [("Edit", self.edit_current), ("Move", self.move_current), ("Mark Empty", lambda: self.mark_state("empty", "MARK_EMPTY")), ("Mark Disposed", lambda: self.mark_state("disposed", "MARK_DISPOSED")), ("Archive", lambda: self.mark_state("archived", "ARCHIVE")), ("Open SDS", self.open_sds), ("Search SDS Online", self.search_sds)]:
            b = QPushButton(text); b.clicked.connect(cb); right.addWidget(b)
        right.addStretch(1)
        self.dashboard = DashboardPage(self.db)

    def refresh(self):
        rows = self.db.list_chemicals()
        sf = self.status_filter.currentText(); query = self.search.text().lower().strip()
        filtered = []
        for r in rows:
            if sf != "all" and r["status"] != sf:
                continue
            text = " ".join(str(r[k] or "") for k in ["name", "cas", "formula", "supplier", "notes"]).lower()
            if query and query not in text:
                continue
            filtered.append(r)

        self.table.setSortingEnabled(False)
        self.table.blockSignals(True)
        try:
            self.table.clearContents()
            self.table.setRowCount(len(filtered))
            for i, r in enumerate(filtered):
                loc = " / ".join([
                    x for x in [
                        r["location_room"],
                        r["location_cabinet"],
                        r["location_shelf"],
                        r["location_detail"],
                    ]
                    if x
                ])
                vals = [
                    r["name"],
                    r["cas"],
                    r["quantity"],
                    r["unit"],
                    loc,
                    r["physical_state"],
                    r["ghs_codes"],
                    r["status"],
                ]
                for j, v in enumerate(vals):
                    if j == 2:
                        item = NumericTableWidgetItem("" if v is None else str(v))
                    else:
                        item = QTableWidgetItem("" if v is None else str(v))
                    if j == 0:
                        item.setData(Qt.UserRole, r["id"])
                    self.table.setItem(i, j, item)
        finally:
            self.table.blockSignals(False)
            self.table.setSortingEnabled(True)

        if not rows:
            QMessageBox.information(self, "Inventory", "No inventory loaded yet. Import a CSV to begin.")

    def _get_current(self):
        if self.current_id is None: return None
        for r in self.db.list_chemicals():
            if r["id"] == self.current_id: return r
        return None

    def select_row(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return

        row = selected[0].row()
        item = self.table.item(row, 0)
        if item is None:
            return

        self.current_id = item.data(Qt.UserRole)
        r = self._get_current()
        if not r:
            return

        self.details.setText(
            f"{r['name']}\n"
            f"CAS: {r['cas']}\n"
            f"Formula: {r['formula']}\n"
            f"Supplier: {r['supplier']}\n"
            f"Qty: {r['quantity']} {r['unit']}\n"
            f"Location: {r['location_room']}/{r['location_cabinet']}/{r['location_shelf']}/{r['location_detail']}\n"
            f"Hazard: {r['hazard_text']}\n"
            f"GHS: {', '.join(parse_ghs_codes(r['ghs_codes'])) or '-'}\n"
            f"Notes: {r['notes']}\n"
            f"SDS: {r['sds_status']}"
        )

    def add_chemical(self):
        d = ChemicalFormDialog(self)
        if d.exec():
            data = d.get_data(); cid = self.db.add_chemical(data)
            self.db.log_action("ADD", cid, data.get("name", ""), data.get("cas"), "manual add")
            self.refresh()

    def edit_current(self):
        r = self._get_current();
        if not r: return
        d = ChemicalFormDialog(self, dict(r))
        if d.exec():
            data = d.get_data(); self.db.update_chemical(r["id"], data)
            self.db.log_action("EDIT", r["id"], data.get("name") or r["name"], data.get("cas") or r["cas"], "manual edit")
            self.refresh()

    def move_current(self):
        r = self._get_current();
        if not r: return
        d = ChemicalFormDialog(self, dict(r))
        if d.exec():
            data = d.get_data()
            fields = {k: data.get(k) for k in ["location_room","location_cabinet","location_shelf","location_detail"]}
            self.db.update_chemical(r["id"], fields)
            self.db.log_action("MOVE", r["id"], r["name"], r["cas"], "location update")
            self.refresh()

    def mark_state(self, status, action):
        r = self._get_current();
        if not r: return
        self.db.update_chemical(r["id"], {"status": status})
        self.db.log_action(action, r["id"], r["name"], r["cas"], f"set status {status}")
        self.refresh()

    def open_sds(self):
        r = self._get_current();
        if r: open_local_sds(r["sds_local_path"] or "")

    def search_sds(self):
        r = self._get_current();
        if not r: return
        for url in build_search_urls(r["name"], r["cas"]): webbrowser.open(url)

    def show_dashboard(self):
        self.dashboard.refresh()
        self.setCentralWidget(self.dashboard)

    def import_csv_action(self):
        f, _ = QFileDialog.getOpenFileName(self, "Import CSV", str(self.base_dir), "CSV (*.csv)")
        if not f: return
        backup_database(self.db.db_path, self.base_dir / "data/exports")
        n = import_csv(self.db, Path(f))
        QMessageBox.information(self, "Import", f"Imported {n} rows")
        self.refresh()

    def export_all(self):
        f, _ = QFileDialog.getSaveFileName(self, "Export Inventory", str(self.base_dir / "data/exports"), "CSV (*.csv)")
        if f:
            export_rows(self.db.list_chemicals(), Path(f)); self.db.log_action("EXPORT", None, "inventory", None, f)

    def export_active(self):
        f, _ = QFileDialog.getSaveFileName(self, "Export Active", str(self.base_dir / "data/exports"), "CSV (*.csv)")
        if f:
            rows = [r for r in self.db.list_chemicals() if r["status"] == "active"]
            export_rows(rows, Path(f)); self.db.log_action("EXPORT", None, "active inventory", None, f)

    def export_logs(self):
        f, _ = QFileDialog.getSaveFileName(self, "Export Logs", str(self.base_dir / "data/exports"), "CSV (*.csv)")
        if not f: return
        with self.db.connect() as conn:
            rows = conn.execute("SELECT * FROM logs ORDER BY id").fetchall()
        export_rows(rows, Path(f)); self.db.log_action("EXPORT", None, "logs", None, f)

    def backup_action(self):
        b = backup_database(self.db.db_path, self.base_dir / "data/exports")
        QMessageBox.information(self, "Backup", f"Backup: {b}")
