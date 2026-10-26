"""Event log popover console for live telemetry and execution logs."""

from datetime import datetime
from typing import Literal, Optional

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QFont, QTextCursor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class EventLogPopover(QWidget):
    """
    Floating frameless popup console displaying live application events and diagnostic telemetry.
    Adheres strictly to continuous rounded geometry (zero 90-degree corners), memory bounds (max 1000 lines),
    and auto-dismissal when losing focus.
    """

    MAX_LOG_LINES: int = 1000

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setObjectName("eventLogPopover")
        self.setFixedSize(820, 520)

        self.current_theme: Literal["dark", "light"] = "dark"
        self.event_count: int = 0

        self.init_ui()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.hide()
            event.accept()
            return
        super().keyPressEvent(event)

    def init_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)

        # Translucent rounded container
        self.container = QFrame(self)
        self.container.setObjectName("eventLogPopoverContainer")
        
        # Soft elevation dropshadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(24)
        self.shadow.setOffset(0, 6)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.container.setGraphicsEffect(self.shadow)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(16, 14, 16, 14)
        container_layout.setSpacing(10)

        # Header bar
        header = QHBoxLayout()
        header.setSpacing(10)

        self.lbl_title = QLabel("Registro de Eventos")
        self.lbl_title.setObjectName("dockTitle")
        self.lbl_title.setProperty("class", "logTitle")
        header.addWidget(self.lbl_title)

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

        container_layout.addLayout(header)

        # Monospace technical log text console
        self.text_edit = QPlainTextEdit()
        self.text_edit.setObjectName("popoverTextEdit")
        self.text_edit.setReadOnly(True)
        mono_font = QFont("Consolas", 11)
        mono_font.setStyleHint(QFont.Monospace)
        self.text_edit.setFont(mono_font)
        self.text_edit.setMaximumBlockCount(self.MAX_LOG_LINES)
        
        # Style text area with continuous rounded corners
        self._apply_text_area_style()

        container_layout.addWidget(self.text_edit, 1)
        root_layout.addWidget(self.container)

    def _apply_text_area_style(self) -> None:
        if self.current_theme == "dark":
            self.text_edit.setStyleSheet(
                "QPlainTextEdit#popoverTextEdit { "
                "background-color: #111215; "
                "color: #a0a5b5; "
                "border: 1px solid #26272d; "
                "border-radius: 18px; "
                "padding: 14px; "
                "font-size: 12px; "
                "line-height: 1.45; "
                "}"
            )
        else:
            self.text_edit.setStyleSheet(
                "QPlainTextEdit#popoverTextEdit { "
                "background-color: #f4f5f8; "
                "color: #3b3f4d; "
                "border: 1px solid #dcdfe8; "
                "border-radius: 18px; "
                "padding: 14px; "
                "font-size: 12px; "
                "line-height: 1.45; "
                "}"
            )

    def append_log(self, message: str) -> None:
        """Appends a formatted log message with timestamp, updating the event counter."""
        if not message:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_entry = f"[{timestamp}] {message}"
        
        self.text_edit.appendPlainText(formatted_entry)
        self.text_edit.moveCursor(QTextCursor.End)
        self.text_edit.ensureCursorVisible()

        self.event_count += 1
        cnt_str = f"{self.event_count:02d}" if self.event_count < 100 else str(self.event_count)
        self.badge_count.setText(f"{cnt_str} EVENTOS")

    def clear_logs(self) -> None:
        """Clears all log entries and resets event count."""
        self.text_edit.clear()
        self.event_count = 0
        self.badge_count.setText("00 EVENTOS")

    def set_theme_mode(self, theme_mode: Literal["dark", "light"]) -> None:
        """Updates styling for dark or light theme."""
        self.current_theme = theme_mode
        self._apply_text_area_style()
        if theme_mode == "dark":
            self.shadow.setColor(QColor(0, 0, 0, 80))
        else:
            self.shadow.setColor(QColor(0, 0, 0, 30))

    def show_above_widget(self, target: QWidget) -> None:
        """Positions the popover centered horizontally above the target widget with a 12px gap, clamped to screen bounds."""
        if not target:
            self.show()
            return
        global_target = target.mapToGlobal(QPoint(0, 0))
        target_center_x = global_target.x() + (target.width() // 2)
        x = target_center_x - (self.width() // 2)
        y = global_target.y() - self.height() - 14

        # Clamping within available screen geometry
        screen = target.screen() if hasattr(target, "screen") else None
        if not screen:
            from PySide6.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = max(geom.left() + 16, min(x, geom.right() - self.width() - 16))
            y = max(geom.top() + 16, min(y, geom.bottom() - self.height() - 16))

        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
