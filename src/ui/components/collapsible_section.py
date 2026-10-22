"""Collapsible drawer component for advanced controls and lip-sync inspection."""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget
)


class CollapsibleSection(QFrame):
    """
    Retractable collapsible container adhering to Anti-Slop / Hick's Law:
    - Encapsulates secondary / expert controls (waveform, micro-adjustments, miniplayer).
    - Remains collapsed by default to keep the primary single-action pipeline clean.
    - Clickable header toggle with dynamic indicator (▶ / ▼).
    """
    toggled = Signal(bool)

    def __init__(self, title: str = "Ajustes Avançados e Inspeção Labial", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("collapsibleSection")
        self.setProperty("class", "bentoCard")

        self.title_text = title
        self.is_expanded = False

        self._init_ui()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(14, 12, 14, 12)
        self.main_layout.setSpacing(6)

        # Clickable header
        self.btn_toggle = QPushButton(f"▶ {self.title_text}")
        self.btn_toggle.setObjectName("collapsibleHeaderBtn")
        self.btn_toggle.setProperty("class", "collapsibleBtn")
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.setFlat(True)
        self.btn_toggle.clicked.connect(self.toggle)
        self.main_layout.addWidget(self.btn_toggle)

        # Content container (hidden by default)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 8, 0, 0)
        self.content_layout.setSpacing(10)
        self.content_widget.setVisible(False)

        self.main_layout.addWidget(self.content_widget)

    def set_content_widget(self, widget: QWidget):
        """Sets the single child widget for the expandable content area."""
        self.content_layout.addWidget(widget)

    def add_widget(self, widget: QWidget):
        """Appends a widget to the expandable content layout."""
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        """Appends a layout to the expandable content layout."""
        self.content_layout.addLayout(layout)

    def toggle(self):
        """Toggles the expansion state."""
        self.set_expanded(not self.is_expanded)

    def set_expanded(self, expanded: bool):
        """Sets the expansion state explicitly."""
        self.is_expanded = expanded
        self.content_widget.setVisible(self.is_expanded)
        arrow = "▼" if self.is_expanded else "▶"
        self.btn_toggle.setText(f"{arrow} {self.title_text}")
        self.toggled.emit(self.is_expanded)
