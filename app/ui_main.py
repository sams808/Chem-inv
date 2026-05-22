import webbrowser
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QFileDialog, QHBoxLayout, QInputDialog,
                               QLabel, QLineEdit, QMainWindow, QMenuBar, QMessageBox, QPushButton, QStackedWidget,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from .ghs_tools import get_pictogram_path, ghs_label, parse_ghs_codes
from .import_export import backup_database, export_rows, import_csv
from .sds_tools import build_search_urls, open_local_sds
from .ui_dashboard import DashboardPage
from .ui_forms import ChemicalFormDialog
from .ui_logs import LogsPage


class NumericTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except (TypeError, ValueError):
            return super().__lt__(other)


class MainWindow(QMainWindow):
    ADMIN_ONLY_ACTIONS = {"import", "clear", "backup", "delete"}

    def __init__(self, db, base_dir: Path):
        super().__init__()
        self.db = db
        self.base_dir = base_dir
        self.current_id = None
        self.is_admin = False
        self.base_title = "Lab Chemical Inventory Manager"
        self.setWindowTitle(self.base_title)
        self.resize(1280, 800)
        self._menu()
        self._ui()
        self.set_admin_mode(False)
        self.refresh()

    def _menu(self):
        mb = QMenuBar(self); file_menu = mb.addMenu("File")
        self.import_action_ref = file_menu.addAction("Import CSV", self.import_csv_action)
        self.clear_action_ref = file_menu.addAction("Clear Inventory", self.clear_inventory_action)
        file_menu.addAction("Export Inventory CSV", self.export_all)
        file_menu.addAction("Export Active Inventory CSV", self.export_active)
        file_menu.addAction("Export Logs CSV", self.export_logs)
        self.backup_action_ref = file_menu.addAction("Backup Database", self.backup_action)
        mode_menu = mb.addMenu("Mode")
        mode_menu.addAction("Regular", lambda: self.set_admin_mode(False))
        mode_menu.addAction("Admin", self.activate_admin_mode)
        self.setMenuBar(mb)

    def _ui(self):
        c = QWidget(); self.setCentralWidget(c)
        h = QHBoxLayout(c)
        left = QVBoxLayout(); h.addLayout(left, 1)
        b_inv = QPushButton("Inventory"); b_inv.clicked.connect(self.show_inventory); left.addWidget(b_inv)
        b_add = QPushButton("Add Chemical"); b_add.clicked.connect(self.add_chemical); left.addWidget(b_add)
        b_dash = QPushButton("Dashboard"); b_dash.clicked.connect(self.show_dashboard); left.addWidget(b_dash)
        b_logs = QPushButton("Logs"); b_logs.clicked.connect(self.show_logs); left.addWidget(b_logs)
        left.addStretch(1)

        self.stack = QStackedWidget(); h.addWidget(self.stack, 8)
        inv_page = QWidget(); inv_layout = QHBoxLayout(inv_page)
        mid = QVBoxLayout(); inv_layout.addLayout(mid, 6)
        self.search = QLineEdit(); self.search.setPlaceholderText("search")
        self.search.textChanged.connect(self.refresh); mid.addWidget(self.search)
        self.status_filter = QComboBox(); self.status_filter.addItems(["all", "active", "empty", "disposed", "archived", "error_duplicate", "missing_sds"])
        self.status_filter.currentTextChanged.connect(self.refresh); mid.addWidget(self.status_filter)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Name", "CAS", "Quantity", "Unit", "Location", "State", "GHS", "Status"])
        self.table.setColumnWidth(6, 170)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.itemSelectionChanged.connect(self.select_row)
        mid.addWidget(self.table)
        right = QVBoxLayout(); inv_layout.addLayout(right, 3)
        self.details = QLabel("Select chemical"); self.details.setWordWrap(True); right.addWidget(self.details)
        self.ghs_detail_widget = QWidget(); self.ghs_detail_layout = QHBoxLayout(self.ghs_detail_widget); self.ghs_detail_layout.setContentsMargins(0, 0, 0, 0); right.addWidget(self.ghs_detail_widget)
        copy_row = QHBoxLayout();
        b_copy_name = QPushButton("Copy name"); b_copy_name.clicked.connect(self.copy_name)
        b_copy_cas = QPushButton("Copy CAS"); b_copy_cas.clicked.connect(self.copy_cas)
        copy_row.addWidget(b_copy_name); copy_row.addWidget(b_copy_cas); right.addLayout(copy_row)
        for text, cb in [("Edit", self.edit_current), ("Move", self.move_current)]:
            b = QPushButton(text); b.clicked.connect(cb); right.addWidget(b)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_current)
        right.addWidget(self.delete_btn)
        for text, cb in [("Mark Empty", lambda: self.mark_state("empty", "MARK_EMPTY")), ("Mark Disposed", lambda: self.mark_state("disposed", "MARK_DISPOSED")), ("Archive", lambda: self.mark_state("archived", "ARCHIVE")), ("Open SDS", self.open_sds), ("Search SDS Online", self.search_sds)]:
            b = QPushButton(text); b.clicked.connect(cb); right.addWidget(b)
        right.addStretch(1)

        self.dashboard = DashboardPage(self.db)
        self.logs_page = LogsPage(self.db)
        self.stack.addWidget(inv_page)
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.logs_page)

    def current_mode(self) -> str:
        return "Admin" if self.is_admin else "Regular"

    def _update_mode_ui(self):
        self.statusBar().showMessage(f"Mode: {self.current_mode()}")
        self.setWindowTitle(f"{self.base_title} — Mode: {self.current_mode()}")

    def set_admin_mode(self, enabled: bool):
        self.is_admin = enabled
        self._update_mode_ui()
        for action in (self.import_action_ref, self.clear_action_ref, self.backup_action_ref):
            action.setEnabled(enabled)
        if hasattr(self, "delete_btn"):
            self.delete_btn.setEnabled(enabled)

    def require_admin(self, action_name: str) -> bool:
        if action_name not in self.ADMIN_ONLY_ACTIONS or self.is_admin:
            return True
        pin, ok = QInputDialog.getText(self, "Admin PIN", f"{action_name} requires admin. Enter PIN:", QLineEdit.Password)
        if not ok:
            return False
        if self.db.verify_admin_pin(pin):
            self.set_admin_mode(True)
            return True
        QMessageBox.warning(self, "Access denied", "Incorrect admin PIN.")
        return False

    def activate_admin_mode(self):
        if self.is_admin:
            return
        pin, ok = QInputDialog.getText(self, "Admin PIN", "Enter admin PIN:", QLineEdit.Password)
        if not ok:
            self.set_admin_mode(False)
            return
        if self.db.verify_admin_pin(pin):
            self.set_admin_mode(True)
            return
        QMessageBox.warning(self, "Access denied", "Incorrect admin PIN.")
        self.set_admin_mode(False)

    def show_inventory(self):
        self.stack.setCurrentIndex(0)
        self.refresh()

    def show_dashboard(self):
        self.dashboard.refresh()
        self.stack.setCurrentIndex(1)

    def show_logs(self):
        self.logs_page.refresh()
        self.stack.setCurrentWidget(self.logs_page)

    def refresh(self):
        rows = self.db.list_chemicals()
        sf = self.status_filter.currentText(); query = self.search.text().lower().strip()
        filtered = []
        for r in rows:
            if sf == "missing_sds" and r["sds_local_path"]:
                continue
            elif sf != "all" and sf != "missing_sds" and r["status"] != sf:
                continue
            text = " ".join(str(r[k] or "") for k in ["name", "cas", "formula", "supplier", "notes", "hazard_text", "location_code"]).lower()
            if query and query not in text:
                continue
            filtered.append(r)

        self.table.setSortingEnabled(False); self.table.blockSignals(True)
        try:
            self.table.clearContents()
            self.table.setRowCount(0)
            self.table.setRowCount(len(filtered))
            for i, r in enumerate(filtered):
                vals = [r["name"], r["cas"], r["quantity"], r["unit"], r["location_code"], r["physical_state"], None, r["status"]]
                for j, v in enumerate(vals):
                    if j == 6:
                        continue
                    item = NumericTableWidgetItem("" if v is None else str(v)) if j == 2 else QTableWidgetItem("" if v is None else str(v))
                    if j == 0: item.setData(Qt.UserRole, r["id"])
                    self.table.setItem(i, j, item)
                self._set_ghs_cell(i, r["ghs_codes"])
        finally:
            self.table.blockSignals(False); self.table.setSortingEnabled(True)

    def _set_ghs_cell(self, row: int, ghs_codes: str | None):
        codes = parse_ghs_codes(ghs_codes)
        if not codes:
            return
        w = QWidget(); ly = QHBoxLayout(w); ly.setContentsMargins(2, 2, 2, 2); ly.setSpacing(2)
        has_image = False
        for code in codes:
            pic = get_pictogram_path(code, self.base_dir)
            lab = QLabel()
            if pic.exists():
                has_image = True
                lab.setPixmap(QPixmap(str(pic)).scaled(QSize(24, 24), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                lab.setToolTip(f"{code} - {ghs_label(code)}")
            ly.addWidget(lab)
        if not has_image:
            for code in codes:
                fallback = QLabel(code)
                fallback.setToolTip(f"{code} - {ghs_label(code)}")
                ly.addWidget(fallback)
        ly.addStretch(1)
        self.table.setCellWidget(row, 6, w)

    def _get_current(self):
        if self.current_id is None: return None
        for r in self.db.list_chemicals():
            if r["id"] == self.current_id: return r
        return None

    def select_row(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected: return
        item = self.table.item(selected[0].row(), 0)
        if item is None: return
        self.current_id = item.data(Qt.UserRole)
        r = self._get_current()
        if not r: return
        self.details.setText(f"{r['name']}\nCAS: {r['cas']}\nFormula: {r['formula']}\nSupplier: {r['supplier']}\nQty: {r['quantity']} {r['unit']}\nLocation: {r['location_code']}\nHazard: {r['hazard_text']}\nNotes: {r['notes']}\nSDS: {r['sds_status']}")
        while self.ghs_detail_layout.count():
            child = self.ghs_detail_layout.takeAt(0); w = child.widget();
            if w: w.deleteLater()
        for code in parse_ghs_codes(r["ghs_codes"]):
            lbl = QLabel(); pic = get_pictogram_path(code, self.base_dir)
            if pic.exists():
                lbl.setPixmap(QPixmap(str(pic)).scaled(QSize(28, 28), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                lbl.setToolTip(f"{code} - {ghs_label(code)}")
            else:
                lbl.setText(code)
            self.ghs_detail_layout.addWidget(lbl)

    def add_chemical(self):
        d = ChemicalFormDialog(self)
        if d.exec():
            data = d.get_data(); cid = self.db.add_chemical(data)
            self.db.log_action("ADD", cid, data.get("name", ""), data.get("cas"), "manual add", mode=self.current_mode())
            self.refresh()

    def edit_current(self):
        r = self._get_current();
        if not r: return
        d = ChemicalFormDialog(self, dict(r))
        if d.exec():
            data = d.get_data(); self.db.update_chemical(r["id"], data)
            self.db.log_action("EDIT", r["id"], data.get("name") or r["name"], data.get("cas") or r["cas"], "manual edit", mode=self.current_mode())
            self.refresh()

    def move_current(self):
        r = self._get_current();
        if not r: return
        text, ok = QInputDialog.getText(self, "Location", "New location code:", text=r["location_code"] or "")
        if ok:
            self.db.update_chemical(r["id"], {"location_code": text.strip() or None})
            self.db.log_action("MOVE", r["id"], r["name"], r["cas"], "location update", mode=self.current_mode())
            self.refresh()

    def mark_state(self, status, action):
        r = self._get_current();
        if not r: return
        self.db.update_chemical(r["id"], {"status": status})
        self.db.log_action(action, r["id"], r["name"], r["cas"], f"set status {status}", mode=self.current_mode())
        self.refresh()

    def delete_current(self):
        if not self.require_admin("delete"):
            return
        r = self._get_current()
        if not r:
            return
        msg = f"Delete {r['name']} (CAS: {r['cas'] or '-'}) from inventory?"
        if QMessageBox.question(self, "Confirm delete", msg) != QMessageBox.Yes:
            return
        chemical_id = r["id"]
        chemical_name = r["name"]
        chemical_cas = r["cas"]
        self.db.log_action("DELETE", chemical_id, chemical_name, chemical_cas, "manual delete", mode=self.current_mode())
        self.db.delete_chemical(chemical_id)
        self.current_id = None
        self.refresh()

    def open_sds(self):
        r = self._get_current();
        if r: open_local_sds(r["sds_local_path"] or "")

    def search_sds(self):
        r = self._get_current();
        if not r: return
        for url in build_search_urls(r["name"], r["cas"]): webbrowser.open(url)

    def copy_name(self):
        r = self._get_current()
        if r and r["name"]: QApplication.clipboard().setText(r["name"])

    def copy_cas(self):
        r = self._get_current()
        if r and r["cas"]: QApplication.clipboard().setText(r["cas"])

    def clear_inventory_action(self):
        if not self.require_admin("clear"): return
        msg = "Clear all inventory entries? This will remove all chemicals from the local database. A backup will be created first. This cannot be undone from the UI."
        if QMessageBox.question(self, "Confirm clear", msg) != QMessageBox.Yes: return
        text, ok = QInputDialog.getText(self, "Type confirmation", "Type CLEAR to proceed:")
        if not ok or text.strip() != "CLEAR":
            QMessageBox.information(self, "Cancelled", "Clear cancelled.")
            return
        backup_database(self.db.db_path, self.base_dir / "data/exports")
        self.db.clear_inventory(mode=self.current_mode())
        self.refresh()

    def import_csv_action(self):
        if not self.require_admin("import"): return
        f, _ = QFileDialog.getOpenFileName(self, "Import CSV", str(self.base_dir), "CSV (*.csv)")
        if not f: return
        mode, ok = QInputDialog.getItem(self, "Import mode", "Choose import mode:", ["Append to current inventory", "Replace current inventory"], editable=False)
        if not ok: return
        backup_database(self.db.db_path, self.base_dir / "data/exports")
        if mode.startswith("Replace"):
            if QMessageBox.question(self, "Confirm replace", "Replace current inventory with CSV content?") != QMessageBox.Yes:
                return
            self.db.clear_inventory(mode=self.current_mode()); action = "IMPORT_REPLACE"
        else:
            action = "IMPORT_APPEND"
        n = import_csv(self.db, Path(f))
        self.db.log_action(action, None, "inventory", None, f"imported {n} rows from {f}", mode=self.current_mode())
        QMessageBox.information(self, "Import", f"Imported {n} rows")
        self.refresh()

    def export_all(self):
        f, _ = QFileDialog.getSaveFileName(self, "Export Inventory", str(self.base_dir / "data/exports"), "CSV (*.csv)")
        if f:
            export_rows(self.db.list_chemicals(), Path(f)); self.db.log_action("EXPORT", None, "inventory", None, f, mode=self.current_mode())

    def export_active(self):
        f, _ = QFileDialog.getSaveFileName(self, "Export Active", str(self.base_dir / "data/exports"), "CSV (*.csv)")
        if f:
            rows = [r for r in self.db.list_chemicals() if r["status"] == "active"]
            export_rows(rows, Path(f)); self.db.log_action("EXPORT", None, "active inventory", None, f, mode=self.current_mode())

    def export_logs(self):
        f, _ = QFileDialog.getSaveFileName(self, "Export Logs", str(self.base_dir / "data/exports"), "CSV (*.csv)")
        if not f: return
        with self.db.connect() as conn:
            rows = conn.execute("SELECT * FROM logs ORDER BY id").fetchall()
        export_rows(rows, Path(f)); self.db.log_action("EXPORT", None, "logs", None, f, mode=self.current_mode())

    def backup_action(self):
        if not self.require_admin("backup"): return
        b = backup_database(self.db.db_path, self.base_dir / "data/exports")
        self.db.log_action(
            "BACKUP",
            None,
            "database",
            None,
            str(b),
            mode=self.current_mode(),
        )
        QMessageBox.information(self, "Backup", f"Backup: {b}")
