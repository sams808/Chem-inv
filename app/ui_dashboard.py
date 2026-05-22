from collections import Counter

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .cas_tools import is_valid_cas_format
from .ghs_tools import parse_ghs_codes


class DashboardPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.layout = QVBoxLayout(self)
        self.refresh_btn = QPushButton("Refresh Dashboard")
        self.refresh_btn.clicked.connect(self.refresh)
        self.layout.addWidget(self.refresh_btn)

        self.cards = {}
        cards_widget = QWidget()
        self.cards_layout = QGridLayout(cards_widget)
        self.layout.addWidget(cards_widget)
        for idx, key in enumerate(["Total", "Active", "Missing SDS", "Missing CAS", "Suspicious CAS", "Archived/Disposed"]):
            card = QFrame()
            card.setFrameShape(QFrame.StyledPanel)
            card_layout = QVBoxLayout(card)
            title = QLabel(key)
            value = QLabel("0")
            value.setStyleSheet("font-size: 22px; font-weight: bold;")
            card_layout.addWidget(title)
            card_layout.addWidget(value)
            self.cards[key] = value
            self.cards_layout.addWidget(card, idx // 3, idx % 3)

        self.action_needed = QLabel()
        self.action_needed.setWordWrap(True)
        self.layout.addWidget(self.action_needed)

        self.canvas = FigureCanvas(Figure(figsize=(9, 6)))
        self.layout.addWidget(self.canvas, 1)

    def refresh(self):
        rows = self.db.list_chemicals()
        total = len(rows)
        active = sum(1 for r in rows if r["status"] == "active")
        missing_cas = sum(1 for r in rows if not r["cas"])
        suspicious = sum(1 for r in rows if r["cas"] and not is_valid_cas_format(r["cas"]))
        missing_sds = sum(1 for r in rows if not r["sds_local_path"])
        archived_disposed = sum(1 for r in rows if r["status"] in {"archived", "disposed"})

        values = {
            "Total": total,
            "Active": active,
            "Missing SDS": missing_sds,
            "Missing CAS": missing_cas,
            "Suspicious CAS": suspicious,
            "Archived/Disposed": archived_disposed,
        }
        for key, value in values.items():
            self.cards[key].setText(str(value))

        self.action_needed.setText(
            "Action needed: "
            f"{missing_sds} products missing SDS; "
            f"{missing_cas} products missing CAS; "
            f"{suspicious} suspicious CAS entries."
        )

        fig = self.canvas.figure
        fig.clear()
        if not rows:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "No inventory loaded", ha="center", va="center")
            ax.set_axis_off()
            self.canvas.draw_idle()
            return

        ax1 = fig.add_subplot(221)
        ax2 = fig.add_subplot(222)
        ax3 = fig.add_subplot(223)
        ax4 = fig.add_subplot(224)

        status = Counter((r["status"] or "unknown") for r in rows)
        ax1.bar(list(status.keys()), list(status.values()))
        ax1.set_title("Count by status")
        ax1.tick_params(axis="x", rotation=25)

        ghs_counter = Counter()
        for r in rows:
            for code in parse_ghs_codes(r["ghs_codes"]):
                ghs_counter[code] += 1
        if ghs_counter:
            ax2.bar(list(ghs_counter.keys()), list(ghs_counter.values()))
        ax2.set_title("Count by GHS")
        ax2.tick_params(axis="x", rotation=25)

        loc_counter = Counter((r["location_code"] or "(empty)") for r in rows)
        top_loc = loc_counter.most_common(10)
        if top_loc:
            ax3.bar([x[0] for x in top_loc], [x[1] for x in top_loc])
        ax3.set_title("Top locations")
        ax3.tick_params(axis="x", rotation=35)

        problems = {
            "Missing SDS": missing_sds,
            "Missing CAS": missing_cas,
            "Suspicious CAS": suspicious,
        }
        ax4.bar(list(problems.keys()), list(problems.values()))
        ax4.set_title("Problems overview")
        ax4.tick_params(axis="x", rotation=20)

        fig.tight_layout()
        self.canvas.draw_idle()
