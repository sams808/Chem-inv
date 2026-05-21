from collections import Counter

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .cas_tools import is_valid_cas_format
from .ghs_tools import parse_ghs_codes


class DashboardPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.layout = QVBoxLayout(self)
        self.summary = QLabel()
        self.layout.addWidget(self.summary)
        self.canvas = FigureCanvas(Figure(figsize=(7, 5)))
        self.layout.addWidget(self.canvas)

    def refresh(self):
        rows = self.db.list_chemicals()
        total = len(rows)
        active = sum(1 for r in rows if r["status"] == "active")
        missing_cas = sum(1 for r in rows if not r["cas"])
        suspicious = sum(1 for r in rows if r["cas"] and not is_valid_cas_format(r["cas"]))
        missing_sds = sum(1 for r in rows if not r["sds_local_path"])
        self.summary.setText(f"Total:{total} Active:{active} Missing CAS:{missing_cas} Suspicious CAS:{suspicious} Missing SDS:{missing_sds}")

        fig = self.canvas.figure
        fig.clear()
        ax1 = fig.add_subplot(221)
        ax2 = fig.add_subplot(222)
        ax3 = fig.add_subplot(212)

        status = Counter((r["status"] or "unknown") for r in rows)
        ax1.bar(list(status.keys()), list(status.values())); ax1.set_title("Count by status")

        ghs_counter = Counter()
        for r in rows:
            for code in parse_ghs_codes(r["ghs_codes"]):
                ghs_counter[code] += 1
        ax2.bar(list(ghs_counter.keys()), list(ghs_counter.values())); ax2.set_title("Count by GHS")

        loc_counter = Counter((r["location_code"] or "(empty)") for r in rows)
        top_loc = loc_counter.most_common(10)
        if top_loc:
            ax3.bar([x[0] for x in top_loc], [x[1] for x in top_loc]); ax3.set_title("Top locations")
        ax3.tick_params(axis='x', rotation=30)
        fig.tight_layout()
        self.canvas.draw_idle()
