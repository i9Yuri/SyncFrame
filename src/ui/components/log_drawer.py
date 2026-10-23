"""Retractable terminal event log drawer for diagnostic monitoring."""

from datetime import datetime
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
    Collapsible event log console adhering to Workbench precision specs:
    - Fixed base drawer
    - Formatted entries with timestamps and status indicators
    - Expand / Collapse toggle with event counter badge
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("bentoCard")
        self.setProperty("class", "bentoCard")
        self.is_expanded: bool = False
        self.event_count: int = 0

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 10, 16, 10)

        header = QHBoxLayout()
        header.setSpacing(10)

        self.title_lbl = QLabel("Event log")
        self.title_lbl.setStyleSheet("color: #eef0f2; font-weight: 700; font-size: 12px;")
        header.addWidget(self.title_lbl)

        self.badge_count = QLabel("00 EVENTS")
        self.badge_count.setProperty("class", "badgeNeutral")
        header.addWidget(self.badge_count)

        header.addStretch()

        self.btn_clear = QPushButton("Limpar")
        self.btn_clear.setProperty("class", "btnSecondary")
        self.btn_clear.setFixedWidth(70)
        self.btn_clear.clicked.connect(self.clear_logs)
        header.addWidget(self.btn_clear)

        self.btn_toggle = QPushButton("Expandir ▲")
        self.btn_toggle.setProperty("class", "btnSecondary")
        self.btn_toggle.setFixedWidth(110)
        self.btn_toggle.clicked.connect(self.toggle_collapse)
        header.addWidget(self.btn_toggle)

        layout.addLayout(header)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumHeight(160)
        self.text_edit.setVisible(False)
        layout.addWidget(self.text_edit)

    def toggle_collapse(self):
        self.is_expanded = not self.is_expanded
        self.text_edit.setVisible(self.is_expanded)
        self.btn_toggle.setText("Recolher ▼" if self.is_expanded else "Expandir ▲")

    def append_log(self, message: str):
        now_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_entry = f"{now_str}  ●  {message}"
        self.text_edit.appendPlainText(formatted_entry)
        self.event_count += 1
        self.badge_count.setText(f"{self.event_count:02d} EVENTS")

        # Auto-scroll to bottom
        sb = self.text_edit.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear_logs(self):
        self.text_edit.clear()
        self.event_count = 0
        self.badge_count.setText("00 EVENTS")
