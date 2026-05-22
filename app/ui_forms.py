from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QGridLayout,
                               QHBoxLayout, QLineEdit, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget)

from .ghs_tools import ALLOWED_GHS, get_pictogram_path, ghs_label, parse_ghs_codes, sort_ghs_codes, validate_ghs_codes


class ChemicalFormDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Chemical")
        self.fields = {}
        self.ghs_buttons = {}
        self.selected_ghs = set()
        data = data or {}
        layout = QVBoxLayout(self)
        form = QFormLayout()
        for name in ["name", "cas", "formula", "supplier"]:
            w = QLineEdit(str(data.get(name, "") or ""))
            self.fields[name] = w
            form.addRow(name, w)

        self.physical_state = QComboBox()
        self.physical_state.addItems(["solid", "liquid", "gas"])
        existing_state = str(data.get("physical_state") or "").strip().lower()
        if existing_state in {"solid", "liquid", "gas"}:
            self.physical_state.setCurrentText(existing_state)
        elif existing_state:
            self.physical_state.addItem(existing_state)
            self.physical_state.setCurrentText(existing_state)
        form.addRow("physical_state", self.physical_state)

        self.quantity = QDoubleSpinBox(); self.quantity.setMaximum(1e9); self.quantity.setValue(float(data.get("quantity") or 0)); form.addRow("quantity", self.quantity)
        self.unit = QLineEdit(str(data.get("unit", "") or "")); form.addRow("unit", self.unit)

        for name in ["location_code"]:
            w = QLineEdit(str(data.get(name, "") or ""))
            self.fields[name] = w
            form.addRow(name, w)

        ghs_wrap = QWidget()
        ghs_layout = QGridLayout(ghs_wrap)
        base_dir = getattr(parent, "base_dir", None)
        for idx, code in enumerate(ALLOWED_GHS):
            btn = QPushButton(code)
            btn.setCheckable(True)
            btn.setToolTip(f"{code} - {ghs_label(code)}")
            if base_dir:
                picto = get_pictogram_path(code, base_dir)
                if picto.exists():
                    btn.setIcon(QIcon(str(picto)))
                    btn.setIconSize(QSize(28, 28))
            btn.toggled.connect(self._update_ghs_style)
            ghs_layout.addWidget(btn, idx // 3, idx % 3)
            self.ghs_buttons[code] = btn
        form.addRow("ghs_codes", ghs_wrap)

        self.hazard = QTextEdit(data.get("hazard_text") or ""); form.addRow("hazard_text", self.hazard)
        self.notes = QTextEdit(data.get("notes") or ""); form.addRow("notes", self.notes)

        for name in ["sds_local_path", "sds_url", "sds_status"]:
            w = QLineEdit(str(data.get(name, "") or ""))
            self.fields[name] = w
            form.addRow(name, w)

        self.status = QComboBox(); self.status.addItems(["active", "empty", "disposed", "archived", "error_duplicate"]); self.status.setCurrentText(data.get("status", "active")); form.addRow("status", self.status)

        layout.addLayout(form)
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        layout.addWidget(bb)
        self._set_ghs_from_text(data.get("ghs_codes"))

    def _set_ghs_from_text(self, text):
        for code in parse_ghs_codes(text):
            if code in self.ghs_buttons:
                self.ghs_buttons[code].setChecked(True)
        self._update_ghs_style()

    def _update_ghs_style(self):
        self.selected_ghs = {code for code, btn in self.ghs_buttons.items() if btn.isChecked()}
        for code, btn in self.ghs_buttons.items():
            btn.setStyleSheet("border: 2px solid #2e7d32; background-color: #e8f5e9;" if code in self.selected_ghs else "")

    def get_data(self):
        d = {k: (v.text().strip() or None) for k, v in self.fields.items()}
        d["physical_state"] = self.physical_state.currentText()
        d["quantity"] = self.quantity.value() if self.quantity.value() else None
        d["unit"] = self.unit.text().strip() or None
        d["status"] = self.status.currentText()
        d["hazard_text"] = self.hazard.toPlainText().strip() or None
        d["notes"] = self.notes.toPlainText().strip() or None
        ghs_codes = sort_ghs_codes(list(self.selected_ghs))
        d["ghs_codes"] = ";".join(ghs_codes) if ghs_codes else None
        invalid = validate_ghs_codes(d.get("ghs_codes"))
        if invalid:
            QMessageBox.warning(self, "Warning", f"Invalid GHS codes: {', '.join(invalid)}")
        return d
