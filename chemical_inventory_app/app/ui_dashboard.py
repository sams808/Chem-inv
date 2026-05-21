from collections import Counter

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .cas_tools import is_valid_cas_format


class DashboardPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.layout = QVBoxLayout(self)
        self.summary = QLabel()
        self.layout.addWidget(self.summary)
        self.canvas = FigureCanvas(Figure(figsize=(6, 3)))
        self.layout.addWidget(self.canvas)

    def refresh(self):
        rows = self.db.list_chemicals()
        total = len(rows)
        active = sum(1 for r in rows if r["status"] == "active")
        empty_disposed = sum(1 for r in rows if r["status"] in {"empty", "disposed"})
        missing_cas = sum(1 for r in rows if not r["cas"])
        suspicious = sum(1 for r in rows if r["cas"] and not is_valid_cas_format(r["cas"]))
        missing_sds = sum(1 for r in rows if not r["sds_local_path"])
        self.summary.setText(f"Total:{total} Active:{active} Empty/Disposed:{empty_disposed} Missing CAS:{missing_cas} Suspicious CAS:{suspicious} Missing SDS:{missing_sds}")
        ax = self.canvas.figure.subplots(); ax.clear()
        c = Counter((r["status"] or "unknown") for r in rows)
        ax.bar(list(c.keys()), list(c.values())); ax.set_title("Count by status")
        self.canvas.draw_idle()
