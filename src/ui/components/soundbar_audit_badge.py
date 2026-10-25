"""Reactive 7.1.4 immersive soundbar compatibility audit badge with smooth fade tooltip."""

import logging
from typing import Optional

from PySide6.QtCore import Qt, QPoint, QEasingCurve, QPropertyAnimation
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget
)

from ...core.models import ImmersiveAuditResult

logger = logging.getLogger(__name__)


class SmoothFadeTooltip(QWidget):
    """
    Lightweight frameless tooltip with smooth opacity fade transition (120ms, OutQuad)
    and strict One UI rounded geometry (12px continuous radius).
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            parent,
            Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.current_theme = "dark"

        # Opacity effect and animation setup
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self.opacity_effect)

        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity", self)
        self.fade_anim.setDuration(120)
        self.fade_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.fade_anim.finished.connect(self._on_animation_finished)

        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.container = QFrame(self)
        self.container.setObjectName("soundbarTooltipContainer")
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(3)

        # Line 1: Device & Mode status
        self.lbl_title = QLabel()
        self.lbl_title.setObjectName("lblTooltipTitle")
        f_title = QFont()
        f_title.setPointSize(10)
        f_title.setBold(True)
        self.lbl_title.setFont(f_title)
        layout.addWidget(self.lbl_title)

        # Line 2: Technical acoustic diagnosis
        self.lbl_desc = QLabel()
        self.lbl_desc.setObjectName("lblTooltipDesc")
        f_desc = QFont()
        f_desc.setPointSize(9)
        self.lbl_desc.setFont(f_desc)
        self.lbl_desc.setWordWrap(False)
        layout.addWidget(self.lbl_desc)

        # Line 3: Actionable suggestion
        self.lbl_sug = QLabel()
        self.lbl_sug.setObjectName("lblTooltipSug")
        f_sug = QFont()
        f_sug.setPointSize(8)
        self.lbl_sug.setFont(f_sug)
        self.lbl_sug.setWordWrap(False)
        layout.addWidget(self.lbl_sug)

        root.addWidget(self.container)
        self._apply_theme_styling()

    def _apply_theme_styling(self):
        if self.current_theme == "light":
            self.container.setStyleSheet(
                "QFrame#soundbarTooltipContainer {"
                "    background-color: #ffffff;"
                "    border: 1px solid #dcdfe8;"
                "    border-radius: 12px;"
                "}"
                "QLabel#lblTooltipTitle { color: #16181d; background: transparent; border: none; font-weight: 700; }"
                "QLabel#lblTooltipDesc { color: #555a68; background: transparent; border: none; }"
                "QLabel#lblTooltipSug { color: #6a7080; background: transparent; border: none; }"
            )
        else:
            self.container.setStyleSheet(
                "QFrame#soundbarTooltipContainer {"
                "    background-color: #1c1d22;"
                "    border: 1px solid #33343b;"
                "    border-radius: 12px;"
                "}"
                "QLabel#lblTooltipTitle { color: #f2f3f7; background: transparent; border: none; font-weight: 700; }"
                "QLabel#lblTooltipDesc { color: #9a9eac; background: transparent; border: none; }"
                "QLabel#lblTooltipSug { color: #707584; background: transparent; border: none; }"
            )

    def set_theme_mode(self, theme: str):
        self.current_theme = theme
        self._apply_theme_styling()

    def display_at(self, global_anchor: QPoint, result: Optional[ImmersiveAuditResult]):
        if result is None:
            self.hide_tooltip()
            return

        self.lbl_title.setText(result.title)
        self.lbl_desc.setText(result.description)
        self.lbl_sug.setText(result.suggestion)

        # Ensure exact bounding width via QFontMetrics + padding
        fm_title = self.lbl_title.fontMetrics().horizontalAdvance(result.title)
        fm_desc = self.lbl_desc.fontMetrics().horizontalAdvance(result.description)
        fm_sug = self.lbl_sug.fontMetrics().horizontalAdvance(result.suggestion)
        needed_w = max(fm_title, fm_desc, fm_sug) + 32
        needed_h = self.layout().sizeHint().height()

        self.setFixedSize(max(needed_w, 260), max(needed_h, 70))

        # Position centered above anchor with 8px clearance
        w = self.width()
        h = self.height()
        target_x = global_anchor.x() - (w // 2)
        target_y = global_anchor.y() - h - 8

        # Clamp against screen boundaries
        screen = QGuiApplication.screenAt(global_anchor)
        if screen:
            geo = screen.availableGeometry()
            target_x = max(geo.left() + 10, min(target_x, geo.right() - w - 10))
            if target_y < geo.top() + 10:
                # Flip below anchor if clipping at top
                target_y = global_anchor.y() + 28

        self.move(target_x, target_y)

        # Trigger smooth fade-in
        self.fade_anim.stop()
        self.show()
        self.fade_anim.setStartValue(self.opacity_effect.opacity())
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()

    def hide_tooltip(self):
        if not self.isVisible():
            return
        self.fade_anim.stop()
        self.fade_anim.setStartValue(self.opacity_effect.opacity())
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.start()

    def hide_immediately(self):
        self.fade_anim.stop()
        self.opacity_effect.setOpacity(0.0)
        self.hide()

    def _on_animation_finished(self):
        if self.opacity_effect.opacity() <= 0.01:
            self.hide()


class SoundbarAuditBadge(QWidget):
    """
    Compact 24x24px circular badge auditing 7.1.4 immersive capabilities:
    - Optimal (Green check): Full 7.1.4 / Atmos / lossless spatial utilization.
    - Suboptimal (Amber exclamation): Conventional 5.1, stereo 2.0 or compressed transcode.
    Integrated with SmoothFadeTooltip for actionable technical guidance.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("badgeSoundbarAudit")
        self.setFixedSize(24, 24)
        self.setCursor(Qt.PointingHandCursor)

        self.audit_result: Optional[ImmersiveAuditResult] = None
        self.current_theme: str = "dark"
        self._tooltip: Optional[SmoothFadeTooltip] = None

    @property
    def tooltip_widget(self) -> SmoothFadeTooltip:
        if self._tooltip is None:
            self._tooltip = SmoothFadeTooltip(self.window() or self)
            self._tooltip.set_theme_mode(self.current_theme)
        return self._tooltip

    def set_audit_result(self, result: Optional[ImmersiveAuditResult]) -> None:
        """Sets the active audit result and requests redraw."""
        self.audit_result = result
        self.update()

    def set_theme_mode(self, theme_mode: str) -> None:
        """Synchronizes color tokens with current application theme."""
        self.current_theme = theme_mode
        if self._tooltip:
            self._tooltip.set_theme_mode(theme_mode)
        self.update()

    def enterEvent(self, event):
        super().enterEvent(event)
        if self.audit_result:
            anchor = self.mapToGlobal(QPoint(self.width() // 2, 0))
            self.tooltip_widget.display_at(anchor, self.audit_result)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if self._tooltip:
            self._tooltip.hide_tooltip()

    def hideEvent(self, event):
        super().hideEvent(event)
        if self._tooltip:
            self._tooltip.hide_immediately()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        is_optimal = self.audit_result is not None and self.audit_result.status == "optimal"

        # Circle dimensions
        rect = self.rect().adjusted(1, 1, -1, -1)

        if is_optimal:
            # Green state
            bg_color = QColor(47, 177, 107, 41)  # rgba(47, 177, 107, 0.16)
            border_color = QColor("#2fb16b")
            glyph_color = QColor("#2fb16b") if self.current_theme == "dark" else QColor("#1e7e48")

            # Draw circular surface and 1px border
            painter.setBrush(bg_color)
            painter.setPen(QPen(border_color, 1.0))
            painter.drawEllipse(rect)

            # Draw vector checkmark (✓)
            pen_glyph = QPen(glyph_color, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen_glyph)
            painter.drawLine(QPoint(7, 12), QPoint(10, 16))
            painter.drawLine(QPoint(10, 16), QPoint(17, 8))
        else:
            # Amber/Yellow state
            bg_color = QColor(232, 150, 58, 41)  # rgba(232, 150, 58, 0.16)
            border_color = QColor("#e8963a")
            glyph_color = QColor("#e8963a") if self.current_theme == "dark" else QColor("#b26a1b")

            # Draw circular surface and 1px border
            painter.setBrush(bg_color)
            painter.setPen(QPen(border_color, 1.0))
            painter.drawEllipse(rect)

            # Draw vector exclamation mark (!)
            pen_glyph = QPen(glyph_color, 2.0, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen_glyph)
            # Vertical stroke
            painter.drawLine(QPoint(12, 6), QPoint(12, 13))
            # Dot
            painter.drawPoint(QPoint(12, 17))

        painter.end()
