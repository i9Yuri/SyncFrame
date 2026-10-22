"""Retractable terminal log drawer for diagnostic monitoring."""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget
)


class LogDrawer(QFrame):
    """
    Collapsible log output panel displaying real-time stdout messages from mkvmerge and FFmpeg.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("bentoCard")
        self.setProperty("class", "bentoCard")
        self.is_expanded: bool = False

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(14, 10, 14, 10)

        header = QHBoxLayout()
        self.title_lbl = QLabel("Terminal de Saída & Logs")
        self.title_lbl.setStyleSheet("color: #94a3b8; font-weight: 600; font-size: 12px;")
        header.addWidget(self.title_lbl)
        header.addStretch()

        self.btn_clear = QPushButton("Limpar")
        self.btn_clear.setProperty("class", "btnSecondary")
        self.btn_clear.setFixedWidth(70)
        self.btn_clear.clicked.connect(self.clear_logs)
        header.addWidget(self.btn_clear)

        self.btn_toggle = QPushButton("Expandir ▲")
        self.btn_toggle.setProperty("class", "btnSecondary")
        self.btn_toggle.setFixedWidth(100)
        self.btn_toggle.clicked.connect(self.toggle_collapse)
        header.addWidget(self.btn_toggle)

        layout.addLayout(header)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumHeight(140)
        self.text_edit.setVisible(False)
        layout.addWidget(self.text_edit)

    def toggle_collapse(self):
        self.is_expanded = not self.is_expanded
        self.text_edit.setVisible(self.is_expanded)
        self.btn_toggle.setText("Recolher ▼" if self.is_expanded else "Expandir ▲")

    def append_log(self, message: str):
        self.text_edit.appendPlainText(message)
        # Auto-scroll to bottom
        sb = self.text_edit.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear_logs(self):
        self.text_edit.clear()
