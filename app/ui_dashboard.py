from collections import Counter

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .cas_tools import is_valid_cas_format
from .ghs_tools import parse_ghs_codes


class DashboardPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        header_label = QLabel("Dashboard")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch(1)

        self.refresh_button = QPushButton("Refresh Dashboard")
        self.refresh_button.clicked.connect(self.refresh)
        header_layout.addWidget(self.refresh_button)
        self.layout.addLayout(header_layout)

        self.cards_layout = QGridLayout()
        self.cards_layout.setHorizontalSpacing(10)
        self.cards_layout.setVerticalSpacing(10)
        self.cards = {
            "total": self._make_card("Total chemicals"),
            "active": self._make_card("Active"),
            "missing_sds": self._make_card("Missing SDS"),
            "missing_cas": self._make_card("Missing CAS"),
            "suspicious": self._make_card("Suspicious CAS"),
            "archived_disposed": self._make_card("Archived / Disposed"),
        }

        self.cards_layout.addWidget(self.cards["total"], 0, 0)
        self.cards_layout.addWidget(self.cards["active"], 0, 1)
        self.cards_layout.addWidget(self.cards["missing_sds"], 0, 2)
        self.cards_layout.addWidget(self.cards["missing_cas"], 1, 0)
        self.cards_layout.addWidget(self.cards["suspicious"], 1, 1)
        self.cards_layout.addWidget(self.cards["archived_disposed"], 1, 2)
        self.layout.addLayout(self.cards_layout)

        self.action_summary = QLabel()
        self.action_summary.setStyleSheet("color: #555; font-style: italic;")
        self.layout.addWidget(self.action_summary)

        self.canvas = FigureCanvas(Figure(figsize=(7, 5)))
        self.layout.addWidget(self.canvas)

    def _make_card(self, title):
        card = QLabel(f"{title}\n0")
        card.setStyleSheet(
            "border: 1px solid #cccccc; border-radius: 6px; padding: 10px; "
            "background: #f8f8f8; font-size: 14px;"
        )
        card.setMinimumHeight(64)
        return card

    def _set_card_value(self, key, title, value):
        self.cards[key].setText(f"{title}\n{value}")

    def refresh(self):
        rows = self.db.list_chemicals()
        total = len(rows)
        active = sum(1 for r in rows if r["status"] == "active")
        missing_sds = sum(1 for r in rows if not r["sds_local_path"])
        missing_cas = sum(1 for r in rows if not r["cas"])
        suspicious = sum(1 for r in rows if r["cas"] and not is_valid_cas_format(r["cas"]))
        archived_disposed = sum(
            1 for r in rows if (r["status"] or "").lower() in {"archived", "disposed"}
        )

        self._set_card_value("total", "Total chemicals", total)
        self._set_card_value("active", "Active", active)
        self._set_card_value("missing_sds", "Missing SDS", missing_sds)
        self._set_card_value("missing_cas", "Missing CAS", missing_cas)
        self._set_card_value("suspicious", "Suspicious CAS", suspicious)
        self._set_card_value("archived_disposed", "Archived / Disposed", archived_disposed)

        action_items = []
        if missing_sds:
            action_items.append(f"{missing_sds} missing SDS")
        if missing_cas:
            action_items.append(f"{missing_cas} missing CAS")
        if suspicious:
            action_items.append(f"{suspicious} suspicious CAS")

        if action_items:
            self.action_summary.setText("Action needed: " + " • ".join(action_items))
        else:
            self.action_summary.setText("No immediate dashboard action items.")

        fig = self.canvas.figure
        fig.clear()
        if not rows:
            self.action_summary.setText("No inventory loaded.")
            ax_empty = fig.add_subplot(111)
            ax_empty.axis("off")
            ax_empty.text(
                0.5,
                0.5,
                "No inventory loaded",
                ha="center",
                va="center",
                fontsize=14,
                fontweight="bold",
            )
            fig.tight_layout()
            self.canvas.draw_idle()
            return

        ax1 = fig.add_subplot(221)
        ax2 = fig.add_subplot(222)
        ax3 = fig.add_subplot(223)
        ax4 = fig.add_subplot(224)

        status = Counter((r["status"] or "unknown") for r in rows)
        ax1.bar(list(status.keys()), list(status.values()))
        ax1.set_title("Count by status")

        ghs_counter = Counter()
        for r in rows:
            for code in parse_ghs_codes(r["ghs_codes"]):
                ghs_counter[code] += 1
        ax2.bar(list(ghs_counter.keys()), list(ghs_counter.values()))
        ax2.set_title("Count by GHS")

        loc_counter = Counter((r["location_code"] or "(empty)") for r in rows)
        top_loc = loc_counter.most_common(10)
        if top_loc:
            ax3.bar([x[0] for x in top_loc], [x[1] for x in top_loc])
        ax3.set_title("Top locations")
        ax3.tick_params(axis="x", rotation=30)

        problem_labels = ["Missing SDS", "Missing CAS", "Suspicious CAS"]
        problem_values = [missing_sds, missing_cas, suspicious]
        ax4.bar(problem_labels, problem_values)
        ax4.set_title("Problems overview")
        ax4.tick_params(axis="x", rotation=20)

        fig.tight_layout()
        self.canvas.draw_idle()
