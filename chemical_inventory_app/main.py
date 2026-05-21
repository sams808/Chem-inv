from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.database import DatabaseManager
from app.ui_main import MainWindow
from app.utils import ensure_app_directories


def main() -> int:
    base_dir = Path(__file__).resolve().parent
    ensure_app_directories(base_dir)
    db = DatabaseManager(base_dir / "data" / "inventory.db", base_dir)
    db.initialize()

    app = QApplication(sys.argv)
    window = MainWindow(db, base_dir)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
