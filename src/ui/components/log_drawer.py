"""Floating dock event log drawer for diagnostic monitoring and telemetry."""

from datetime import datetime
from typing import Optional

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class FloatingDockWidget(QFrame):
    """
    Floating dock event log console adhering to One UI continuous ergonomics:
    - Detached floating bottom pill dock with 34px rounded capsule geometry
    - Resting state with active events indicator, event counter badge, and controls
    - Zero-cost fluid expansion animation via QPropertyAnimation (140ms, InOutQuad)
    - Clean typography and strict zero-emoji interface
    """

    RESTING_HEIGHT: int = 56
    EXPANDED_HEIGHT: int = 220

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("floatingDock")
        self.setProperty("class", "floatingDock")
        self.is_expanded: bool = False
        self.event_count: int = 0
        self._anim: Optional[QPropertyAnimation] = None

        self.init_ui()

    def init_ui(self) -> None:
        self.setFixedHeight(self.RESTING_HEIGHT)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 10, 20, 10)

        # Header resting row
        header = QHBoxLayout()
        header.setSpacing(10)

        # Pulse / active event indicator dot
        self.dot_indicator = QLabel()
        self.dot_indicator.setObjectName("dockIndicatorDot")
        self.dot_indicator.setProperty("class", "greenDot")
        self.dot_indicator.setFixedSize(8, 8)
        header.addWidget(self.dot_indicator)

        self.title_lbl = QLabel("Registro de eventos")
        self.title_lbl.setObjectName("dockTitle")
        self.title_lbl.setProperty("class", "logTitle")
        header.addWidget(self.title_lbl)

        self.badge_count = QLabel("00 EVENTOS")
        self.badge_count.setObjectName("badgeEventCount")
        self.badge_count.setProperty("class", "systemChip")
        self.badge_count.setFixedHeight(28)
        self.badge_count.setAlignment(Qt.AlignCenter)
        header.addWidget(self.badge_count)

        header.addStretch()

        self.btn_clear = QPushButton("Limpar")
        self.btn_clear.setObjectName("btnDockClear")
        self.btn_clear.setProperty("class", "btnSecondary")
        self.btn_clear.setFixedHeight(34)
        self.btn_clear.setFixedWidth(78)
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_logs)
        header.addWidget(self.btn_clear)

        self.btn_toggle = QPushButton("Expandir")
        self.btn_toggle.setObjectName("btnDockToggle")
        self.btn_toggle.setProperty("class", "btnSecondary")
        self.btn_toggle.setFixedHeight(34)
        self.btn_toggle.setFixedWidth(100)
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.clicked.connect(lambda: self.toggle_expansion())
        header.addWidget(self.btn_toggle)

        layout.addLayout(header)

        # Expandable log text viewer
        self.text_edit = QPlainTextEdit()
        self.text_edit.setObjectName("dockTextEdit")
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumHeight(150)
        self.text_edit.setVisible(False)
        layout.addWidget(self.text_edit)

    def toggle_expansion(self, expand: Optional[bool] = None) -> None:
        """
        Toggles or sets the expansion state with smooth 140ms InOutQuad animation.
        Contract: FloatingDockWidget.toggle_expansion(expand: Optional[bool] = None) -> None
        """
        target_state = not self.is_expanded if expand is None else bool(expand)
        if target_state == self.is_expanded:
            return

        self.is_expanded = target_state

        if self._anim and self._anim.state() == QPropertyAnimation.Running:
            self._anim.stop()

        start_h = self.height()
        target_h = self.EXPANDED_HEIGHT if self.is_expanded else self.RESTING_HEIGHT

        # Ensure text edit visibility
        if self.is_expanded:
            self.text_edit.setVisible(True)

        self.btn_toggle.setText("Recolher" if self.is_expanded else "Expandir")

        self.setMinimumHeight(self.RESTING_HEIGHT)
        self.setMaximumHeight(max(start_h, target_h))

        self._anim = QPropertyAnimation(self, b"maximumHeight")
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._anim.setStartValue(start_h)
        self._anim.setEndValue(target_h)

        def _on_anim_finished():
            self.setFixedHeight(target_h)
            if not self.is_expanded:
                self.text_edit.setVisible(False)

        self._anim.finished.connect(_on_anim_finished)
        self._anim.start()

    def toggle_collapse(self) -> None:
        """Compatibility wrapper for toggle_expansion."""
        self.toggle_expansion()

    def append_log(self, message: str) -> None:
        """Appends a timestamped log entry and auto-scrolls to latest message."""
        now_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_entry = f"{now_str}  [EVENT]  {message}"
        self.text_edit.appendPlainText(formatted_entry)
        self.event_count += 1
        self.badge_count.setText(f"{self.event_count:02d} EVENTOS")

        sb = self.text_edit.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear_logs(self) -> None:
        """Clears all accumulated log messages and resets counter."""
        self.text_edit.clear()
        self.event_count = 0
        self.badge_count.setText("00 EVENTOS")


# Backward compatibility alias
LogDrawer = FloatingDockWidget
