from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLineEdit, QMessageBox, QTextEdit, QVBoxLayout

from .ghs_tools import validate_ghs_codes


class ChemicalFormDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Chemical")
        self.fields = {}
        data = data or {}
        layout = QVBoxLayout(self)
        form = QFormLayout()
        for name in ["name","cas","formula","supplier","unit","physical_state","location_room","location_cabinet","location_shelf","location_detail","ghs_codes","sds_local_path","sds_url","sds_status"]:
            w = QLineEdit(str(data.get(name, "") or ""))
            self.fields[name] = w
            form.addRow(name, w)
        self.quantity = QDoubleSpinBox(); self.quantity.setMaximum(1e9); self.quantity.setValue(float(data.get("quantity") or 0)); form.addRow("quantity", self.quantity)
        self.status = QComboBox(); self.status.addItems(["active","empty","disposed","archived","error_duplicate"]); self.status.setCurrentText(data.get("status", "active")); form.addRow("status", self.status)
        self.hazard = QTextEdit(data.get("hazard_text") or ""); form.addRow("hazard_text", self.hazard)
        self.notes = QTextEdit(data.get("notes") or ""); form.addRow("notes", self.notes)
        layout.addLayout(form)
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        layout.addWidget(bb)

    def get_data(self):
        d = {k: (v.text().strip() or None) for k, v in self.fields.items()}
        d["quantity"] = self.quantity.value() if self.quantity.value() else None
        d["status"] = self.status.currentText()
        d["hazard_text"] = self.hazard.toPlainText().strip() or None
        d["notes"] = self.notes.toPlainText().strip() or None
        invalid = validate_ghs_codes(d.get("ghs_codes"))
        if invalid:
            QMessageBox.warning(self, "Warning", f"Invalid GHS codes: {', '.join(invalid)}")
        return d
