from pathlib import Path

from PySide6.QtWidgets import QDialog, QPushButton, QTextBrowser, QVBoxLayout


class UserManualDialog(QDialog):
    def __init__(self, base_dir: Path, parent=None):
        super().__init__(parent)
        self.base_dir = Path(base_dir)
        self.setWindowTitle("Chem-inv User Manual")
        self.resize(900, 700)

        layout = QVBoxLayout(self)
        self.viewer = QTextBrowser(self)
        self.viewer.setReadOnly(True)
        layout.addWidget(self.viewer)

        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self._load_manual()

    def _load_manual(self):
        manual_path = self.base_dir / "docs" / "user_manual.md"
        if not manual_path.exists():
            self.viewer.setPlainText(
                "User manual file not found.\n\n"
                f"Expected location:\n{manual_path}"
            )
            return

        markdown_text = manual_path.read_text(encoding="utf-8")
        if hasattr(self.viewer, "setMarkdown"):
            self.viewer.setMarkdown(markdown_text)
        else:
            self.viewer.setPlainText(markdown_text)
