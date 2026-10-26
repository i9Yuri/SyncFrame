"""
Custom QComboBox and item delegate providing visual highlight for best-quality streams
with 100% continuous rounded corners, high-contrast monochrome tokens and zero saturated accents.
"""

import os
from typing import Optional, Any
from PySide6.QtCore import Qt, QRectF, QSize, QModelIndex
from PySide6.QtGui import QPainter, QColor, QFont, QFontMetrics, QPainterPath
from PySide6.QtWidgets import (
    QApplication,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QWidget,
    QComboBox,
    QStyle,
    QFrame
)
from src.core.models import StreamCandidate


def configure_translucent_combobox_popup(combobox: QComboBox) -> None:
    """
    Configures the popup window of a QComboBox to support 100% continuous rounded corners
    without square background artifacts or white corners poking out from behind the view.
    """
    view = combobox.view()
    if not view:
        return
    container = view.window()
    if container:
        container.setAttribute(Qt.WA_TranslucentBackground, True)
        container.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        if isinstance(container, QFrame):
            container.setFrameShape(QFrame.NoFrame)
            container.setLineWidth(0)
            container.setObjectName("QComboBoxPrivateContainer")
            container.setStyleSheet("#QComboBoxPrivateContainer { background: transparent; border: none; }")


class DropdownHighlightDelegate(QStyledItemDelegate):
    """
    Renders combobox popup items with an elevated surface and rounded monochrome micro-pill
    ('MELHOR QUALIDADE' or 'RECOMENDADO') for the highest-fidelity audio/video streams.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        base_size = super().sizeHint(option, index)
        return QSize(base_size.width(), max(38, base_size.height()))

    def _is_dark(self, option: QStyleOptionViewItem) -> bool:
        parent = self.parent()
        if parent:
            win = parent.window()
            if hasattr(win, "current_theme"):
                return getattr(win, "current_theme", "dark") == "dark"
        app = QApplication.instance()
        if app:
            for w in app.topLevelWidgets():
                if hasattr(w, "current_theme"):
                    return getattr(w, "current_theme", "dark") == "dark"
        return option.palette.window().color().lightness() < 128

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        try:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)

            data = index.data(Qt.UserRole)
            is_best = False
            badge_text = "MELHOR QUALIDADE"

            if isinstance(data, StreamCandidate):
                if data.is_best_quality or data.is_recommended:
                    is_best = True
                    if data.is_recommended and not data.is_best_quality:
                        badge_text = "RECOMENDADO"
            elif isinstance(data, dict):
                is_best = bool(data.get("is_best_quality", False) or data.get("is_recommended", False))
                badge_text = str(data.get("badge_text", "MELHOR QUALIDADE"))

            rect = QRectF(option.rect).adjusted(4, 2, -4, -2)
            is_selected = bool(option.state & QStyle.State_Selected)
            is_hover = bool(option.state & QStyle.State_MouseOver)
            is_dark = self._is_dark(option)

            # Background rendering
            path = QPainterPath()
            path.addRoundedRect(rect, 10.0, 10.0)

            if is_best:
                if is_dark:
                    bg_color = QColor("#323743") if (is_selected or is_hover) else QColor("#282b34")
                    border_color = QColor("#52596b") if (is_selected or is_hover) else QColor("#3e4452")
                    text_color = QColor("#ffffff")
                    pill_bg = QColor("#3e4452")
                    pill_border = QColor("#636b7e")
                    pill_text = QColor("#f3f4f6")
                else:
                    bg_color = QColor("#d8dce6") if (is_selected or is_hover) else QColor("#e4e7ef")
                    border_color = QColor("#a6adb9") if (is_selected or is_hover) else QColor("#c2c7d4")
                    text_color = QColor("#16181d")
                    pill_bg = QColor("#d0d4e0")
                    pill_border = QColor("#9ca3af")
                    pill_text = QColor("#16181d")

                painter.fillPath(path, bg_color)
                painter.setPen(border_color)
                painter.drawPath(path)
            else:
                if is_selected or is_hover:
                    bg_color = QColor("#2a2d36") if is_dark else QColor("#e8ecf4")
                    border_color = QColor("#3a3e4a") if is_dark else QColor("#d4d8e4")
                    text_color = QColor("#f2f3f7") if is_dark else QColor("#16181d")
                    painter.fillPath(path, bg_color)
                    painter.setPen(border_color)
                    painter.drawPath(path)
                else:
                    text_color = QColor("#d1d5db") if is_dark else QColor("#2d3139")

            # Pill badge for best quality option
            pill_width = 0.0
            if is_best:
                badge_font = QFont(option.font)
                badge_font.setPointSize(8)
                badge_font.setBold(True)
                fm = QFontMetrics(badge_font)
                badge_w = fm.horizontalAdvance(badge_text) + 16.0
                badge_h = 22.0
                pill_width = badge_w

                badge_rect = QRectF(
                    rect.right() - badge_w - 8.0,
                    rect.center().y() - (badge_h / 2.0),
                    badge_w,
                    badge_h
                )

                pill_path = QPainterPath()
                pill_path.addRoundedRect(badge_rect, 11.0, 11.0)
                painter.fillPath(pill_path, pill_bg)
                painter.setPen(pill_border)
                painter.drawPath(pill_path)

                painter.setFont(badge_font)
                painter.setPen(pill_text)
                painter.drawText(badge_rect, Qt.AlignCenter, badge_text)

            # Main item text
            text_margin_right = (pill_width + 16.0) if is_best else 12.0
            text_rect = QRectF(
                rect.left() + 10.0,
                rect.top(),
                max(10.0, rect.width() - text_margin_right - 10.0),
                rect.height()
            )

            item_font = QFont(option.font)
            item_font.setPointSize(11)
            if is_best:
                item_font.setBold(True)
            painter.setFont(item_font)
            painter.setPen(text_color)

            raw_text = index.data(Qt.DisplayRole) or ""
            fm_item = QFontMetrics(item_font)
            elided_text = fm_item.elidedText(raw_text, Qt.ElideMiddle, int(text_rect.width()))
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, elided_text)

            painter.restore()
        except Exception:
            super().paint(painter, option, index)


class HighlightComboBox(QComboBox):
    """
    QComboBox equipped with DropdownHighlightDelegate, wheel scroll protection,
    and compositor translucency for 100% rounded popup surfaces.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setItemDelegate(DropdownHighlightDelegate(self))
        configure_translucent_combobox_popup(self)

    def showPopup(self) -> None:
        configure_translucent_combobox_popup(self)
        super().showPopup()
        configure_translucent_combobox_popup(self)

    def wheelEvent(self, event) -> None:
        event.ignore()
