"""Compact floating action dock (native TiltedDock transposition) in PySide6/Qt6."""

from dataclasses import dataclass
from typing import Callable, Dict, Literal, Optional

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    QRectF,
    QSize,
    Qt,
    QTimer,
    Property,
)
from PySide6.QtGui import (
    QColor,
    QCursor,
    QFont,
    QFontMetrics,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtSvg import QSvgRenderer

from src.ui.style import get_dock_icon, get_dock_svg_path
from src.ui.components.event_log_popover import EventLogPopover
from src.ui.components.version_info_popover import VersionInfoPopover


@dataclass
class DockItemConfig:
    id: str
    icon_svg: str
    label: str
    tooltip_text: str
    badge_count: Optional[int] = None


class DockItemButton(QPushButton):
    """
    Individual dock action button with smooth spring scaling on hover (OutBack easing),
    depth-layer dimming for siblings, illuminated circular highlight pill, dynamic badge,
    and coordinated micro-tooltip.
    """

    def __init__(self, config: DockItemConfig, dock_ref: 'FloatingActionDock', parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config = config
        self.dock_ref = dock_ref
        self.setObjectName("dockItemBtn")
        self.setProperty("class", "dockItemBtn")
        self.setFixedSize(40, 40)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._scale: float = 1.0
        self._opacity: float = 1.0
        self._is_active_busy: bool = False
        self._activity_angle: int = 0
        self._activity_timer: Optional[QTimer] = None
        self._svg_renderer: Optional[QSvgRenderer] = None

        # Hover spring animation for scale
        self._scale_anim = QPropertyAnimation(self, b"scaleFactor")
        self._scale_anim.setDuration(160)
        self._scale_anim.setEasingCurve(QEasingCurve.OutBack)
        self._scale_anim.setStartValue(1.0)
        self._scale_anim.setEndValue(1.0)

        # Hover opacity animation (depth layer dimming)
        self._opacity_anim = QPropertyAnimation(self, b"buttonOpacity")
        self._opacity_anim.setDuration(160)
        self._opacity_anim.setEasingCurve(QEasingCurve.OutQuad)
        self._opacity_anim.setStartValue(1.0)
        self._opacity_anim.setEndValue(1.0)

        self.setToolTip(self.config.tooltip_text)
        self.update_icon()

    @Property(float)
    def scaleFactor(self) -> float:
        return self._scale

    @scaleFactor.setter
    def scaleFactor(self, val: float) -> None:
        self._scale = val
        self.update()

    @Property(float)
    def buttonOpacity(self) -> float:
        return self._opacity

    @buttonOpacity.setter
    def buttonOpacity(self, val: float) -> None:
        self._opacity = val
        self.update()

    def animate_to(self, target_scale: float, target_opacity: float) -> None:
        """Smoothly animates both scale factor and opacity."""
        self._scale_anim.stop()
        if abs(self._scale - target_scale) > 0.001:
            self._scale_anim.setStartValue(self._scale)
            self._scale_anim.setEndValue(target_scale)
            self._scale_anim.start()
        else:
            self._scale_anim.setEndValue(target_scale)

        self._opacity_anim.stop()
        if abs(self._opacity - target_opacity) > 0.001:
            self._opacity_anim.setStartValue(self._opacity)
            self._opacity_anim.setEndValue(target_opacity)
            self._opacity_anim.start()
        else:
            self._opacity_anim.setEndValue(target_opacity)

    def update_icon(self) -> None:
        theme = getattr(self.dock_ref, "current_theme", "dark")
        svg_path = get_dock_svg_path(self.config.icon_svg, theme)
        self._svg_renderer = QSvgRenderer(svg_path)
        icon = get_dock_icon(self.config.id, theme)
        self.setIcon(icon)
        self.setIconSize(QSize(20, 20))
        self.update()

    def set_activity_state(self, is_active: bool, tooltip_override: Optional[str] = None) -> None:
        self._is_active_busy = is_active
        if is_active:
            if not self._activity_timer:
                self._activity_timer = QTimer(self)
                self._activity_timer.setInterval(40)
                self._activity_timer.timeout.connect(self._rotate_activity)
            self._activity_timer.start()
            if tooltip_override:
                self.config.tooltip_text = tooltip_override
        else:
            if self._activity_timer:
                self._activity_timer.stop()
            self._activity_angle = 0
            self.update()

    def _rotate_activity(self) -> None:
        self._activity_angle = (self._activity_angle + 12) % 360
        self.update()

    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        if self.dock_ref:
            self.dock_ref.on_button_hover_enter(self)
        else:
            self.animate_to(1.35, 1.0)

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        if self.dock_ref:
            self.dock_ref.on_button_hover_leave(self)
        else:
            self.animate_to(1.0, 1.0)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # Apply effective button opacity for depth layers
        painter.setOpacity(max(0.0, min(1.0, self._opacity)))

        cx = self.width() / 2.0
        cy = self.height() / 2.0

        is_hovered = (self._scale > 1.04) or self.underMouse()
        is_pressed = self.isDown()
        is_dark = (getattr(self.dock_ref, "current_theme", "dark") == "dark")

        # Scale and rotation transforms around center
        painter.save()
        painter.translate(cx, cy)
        if abs(self._scale - 1.0) > 0.001:
            painter.scale(self._scale, self._scale)
        if self._is_active_busy and self._activity_angle != 0:
            painter.rotate(self._activity_angle)

        # 1. Illuminated circular highlight pill on hover / pressed
        btn_radius = 14.0
        bg_rect = QRectF(-btn_radius, -btn_radius, btn_radius * 2, btn_radius * 2)

        if is_pressed:
            fill_col = QColor(255, 255, 255, 55) if is_dark else QColor(0, 0, 0, 40)
            painter.setBrush(fill_col)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(bg_rect)
        elif is_hovered:
            fill_col = QColor(255, 255, 255, 36) if is_dark else QColor(0, 0, 0, 24)
            border_col = QColor(255, 255, 255, 60) if is_dark else QColor(0, 0, 0, 40)
            painter.setBrush(fill_col)
            painter.setPen(QPen(border_col, 1.0))
            painter.drawEllipse(bg_rect)

        # 2. Draw SVG icon centered
        icon_size = 18.0
        icon_rect = QRectF(-icon_size / 2.0, -icon_size / 2.0, icon_size, icon_size)
        if self._svg_renderer and self._svg_renderer.isValid():
            self._svg_renderer.render(painter, icon_rect)
        elif not self.icon().isNull():
            pix = self.icon().pixmap(int(icon_size), int(icon_size))
            painter.drawPixmap(icon_rect.toRect(), pix)

        painter.restore()

        # 3. Render Micro-badge if count > 0
        count = self.config.badge_count
        if count is not None and count > 0:
            count_str = "99+" if count > 99 else str(count)
            badge_font = QFont("Inter", 8, QFont.Bold)
            painter.setFont(badge_font)
            fm = QFontMetrics(badge_font)
            text_w = fm.horizontalAdvance(count_str)
            badge_w = max(16, text_w + 6)
            badge_h = 16
            bx = self.width() - badge_w + 2
            by = -2

            painter.setBrush(QColor("#26272d" if is_dark else "#e1e4ed"))
            painter.setPen(QPen(QColor("#33343b" if is_dark else "#cbcfdc"), 1))
            painter.drawRoundedRect(QRectF(bx, by, badge_w, badge_h), 8, 8)

            painter.setPen(QColor("#f2f3f7" if is_dark else "#16181d"))
            painter.drawText(QRectF(bx, by, badge_w, badge_h), Qt.AlignCenter, count_str)

        painter.end()


class FloatingActionDock(QFrame):
    """
    Decoupled compact floating action dock centered at the bottom of the viewport.
    Auto-sizes to content (fit-content) and hosts Event Logs, Update Check, and Version Info.
    """

    DOCK_HEIGHT: int = 52
    ITEM_SPACING: int = 12
    PADDING_X: int = 16
    PADDING_Y: int = 6

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("floatingActionDock")
        self.setProperty("class", "floatingActionDock")
        self.current_theme: Literal["dark", "light"] = "dark"

        self.buttons: Dict[str, DockItemButton] = {}
        self.callbacks: Dict[str, Callable[[], None]] = {}

        # Child popovers
        self.log_popover = EventLogPopover(self)
        self.version_popover = VersionInfoPopover(self)

        self.init_ui()

    def init_ui(self) -> None:
        self.setFixedHeight(self.DOCK_HEIGHT)

        # Elevation DropShadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(0, 4)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(self.shadow)

        self.layout_items = QHBoxLayout(self)
        self.layout_items.setContentsMargins(self.PADDING_X, self.PADDING_Y, self.PADDING_X, self.PADDING_Y)
        self.layout_items.setSpacing(self.ITEM_SPACING)
        self.layout_items.setAlignment(Qt.AlignCenter)

        # Micro-Tooltip label
        self.tooltip_label = QLabel(self.parentWidget() if self.parentWidget() else self)
        self.tooltip_label.setObjectName("dockTooltip")
        self.tooltip_label.setAlignment(Qt.AlignCenter)
        self.tooltip_label.setVisible(False)
        self.tooltip_opacity = QGraphicsOpacityEffect(self.tooltip_label)
        self.tooltip_label.setGraphicsEffect(self.tooltip_opacity)
        self.tooltip_anim = QPropertyAnimation(self.tooltip_opacity, b"opacity")
        self.tooltip_anim.setDuration(120)
        self.tooltip_anim.finished.connect(self._on_tooltip_anim_finished)

        # Floating Toast notification pill
        self.toast_label = QLabel(self.parentWidget() if self.parentWidget() else self)
        self.toast_label.setObjectName("floatingToast")
        self.toast_label.setAlignment(Qt.AlignCenter)
        self.toast_label.setVisible(False)
        self.toast_opacity = QGraphicsOpacityEffect(self.toast_label)
        self.toast_label.setGraphicsEffect(self.toast_opacity)
        self.toast_anim = QPropertyAnimation(self.toast_opacity, b"opacity")
        self.toast_anim.setDuration(160)
        self.toast_anim.finished.connect(self._on_toast_anim_finished)
        self.toast_timer = QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(self._fade_out_toast)

        self._setup_default_tools()

    def _setup_default_tools(self) -> None:
        """Registers the three core dock tools: Event Logs, Check Updates, Version Info."""
        # 1. Event Log Tool
        cfg_log = DockItemConfig(
            id="event_log",
            icon_svg="terminal",
            label="Registro de Eventos",
            tooltip_text="Registro de Eventos",
            badge_count=0,
        )
        self.add_dock_item(cfg_log, self._on_event_log_clicked)

        # 2. Check Updates Tool
        cfg_up = DockItemConfig(
            id="check_updates",
            icon_svg="update",
            label="Verificar Atualizações",
            tooltip_text="Verificar Atualizações",
            badge_count=None,
        )
        self.add_dock_item(cfg_up, self._on_check_updates_clicked)

        # 3. Theme Toggle Tool
        cfg_theme = DockItemConfig(
            id="theme_toggle",
            icon_svg="theme",
            label="Modo Claro" if self.current_theme == "dark" else "Modo Escuro",
            tooltip_text="Modo Claro" if self.current_theme == "dark" else "Modo Escuro",
            badge_count=None,
        )
        self.add_dock_item(cfg_theme, self._on_theme_toggle_clicked)

        # 4. Version Info Tool
        cfg_ver = DockItemConfig(
            id="version_info",
            icon_svg="info",
            label="Versão e Diagnóstico",
            tooltip_text="Versão e Diagnóstico",
            badge_count=None,
        )
        self.add_dock_item(cfg_ver, self._on_version_info_clicked)

    def add_dock_item(self, config: DockItemConfig, on_click: Callable[[], None]) -> None:
        """Adds a new dock item, auto-adjusting the dock width dynamically."""
        btn = DockItemButton(config, self, self)
        btn.clicked.connect(on_click)
        self.buttons[config.id] = btn
        self.callbacks[config.id] = on_click
        self.layout_items.addWidget(btn)
        self._update_dock_geometry()

    def _update_dock_geometry(self) -> None:
        """Calculates exact fit-content width based on children count."""
        num_items = len(self.buttons)
        if num_items == 0:
            self.setFixedWidth(64)
            return
        total_w = (self.PADDING_X * 2) + (num_items * 40) + ((num_items - 1) * self.ITEM_SPACING)
        self.setFixedWidth(total_w)
        self.setFixedHeight(self.DOCK_HEIGHT)

    def update_badge_count(self, item_id: str, count: int) -> None:
        """Updates the badge count for an item."""
        btn = self.buttons.get(item_id)
        if btn:
            btn.config.badge_count = count
            btn.update()

    def set_item_activity_state(self, item_id: str, is_active: bool, tooltip_override: Optional[str] = None) -> None:
        """Sets subtle rotation / activity state on button while working."""
        btn = self.buttons.get(item_id)
        if btn:
            btn.set_activity_state(is_active, tooltip_override)

    def on_button_hover_enter(self, active_btn: DockItemButton) -> None:
        """
        Coordinates hover state across dock items inspired by TiltedDock:
        - Active hovered button scales to 1.35x and retains full opacity (1.0).
        - Non-hovered sibling buttons smoothly dim to 0.45 opacity to focus attention.
        """
        for btn in self.buttons.values():
            if btn is active_btn:
                btn.animate_to(target_scale=1.35, target_opacity=1.0)
            else:
                btn.animate_to(target_scale=1.0, target_opacity=0.45)
        self.show_tooltip(active_btn, active_btn.config.tooltip_text)

    def on_button_hover_leave(self, left_btn: DockItemButton) -> None:
        """Restores all dock buttons to full opacity (1.0) and resting scale (1.0)."""
        for btn in self.buttons.values():
            btn.animate_to(target_scale=1.0, target_opacity=1.0)
        self.hide_tooltip()

    def show_tooltip(self, btn: DockItemButton, text: str) -> None:
        """Displays micro-tooltip pill smoothly positioned above hovered button."""
        if not text:
            return
        parent = self.parentWidget()
        if not parent:
            return

        self.tooltip_label.setText(text)
        fm = self.tooltip_label.fontMetrics()
        w = fm.horizontalAdvance(text) + 24
        self.tooltip_label.setFixedSize(w, 26)

        btn_global = btn.mapToGlobal(QPoint(0, 0))
        parent_pos = parent.mapFromGlobal(btn_global)
        tx = parent_pos.x() + (btn.width() - w) // 2
        ty = parent_pos.y() - 34

        self.tooltip_label.move(tx, ty)
        self.tooltip_label.setVisible(True)
        self.tooltip_label.raise_()

        self.tooltip_anim.stop()
        self.tooltip_anim.setStartValue(self.tooltip_opacity.opacity())
        self.tooltip_anim.setEndValue(1.0)
        self.tooltip_anim.start()

    def hide_tooltip(self) -> None:
        """Fades out micro-tooltip."""
        self.tooltip_anim.stop()
        self.tooltip_anim.setStartValue(self.tooltip_opacity.opacity())
        self.tooltip_anim.setEndValue(0.0)
        self.tooltip_anim.start()

    def _on_tooltip_anim_finished(self) -> None:
        if self.tooltip_opacity.opacity() <= 0.05:
            self.tooltip_label.setVisible(False)

    def show_toast(self, message: str, duration_ms: int = 3000) -> None:
        """Shows a floating notification toast pill above the dock."""
        parent = self.parentWidget()
        if not parent or not message:
            return

        self.toast_label.setText(message)
        fm = self.toast_label.fontMetrics()
        w = fm.horizontalAdvance(message) + 36
        self.toast_label.setFixedSize(w, 36)

        tx = (parent.width() - w) // 2
        ty = self.y() - 46
        self.toast_label.move(tx, ty)
        self.toast_label.setVisible(True)
        self.toast_label.raise_()

        self.toast_anim.stop()
        self.toast_opacity.setOpacity(0.0)
        self.toast_anim.setStartValue(0.0)
        self.toast_anim.setEndValue(1.0)
        self.toast_anim.start()

        self.toast_timer.start(duration_ms)

    def _fade_out_toast(self) -> None:
        self.toast_anim.stop()
        self.toast_anim.setStartValue(self.toast_opacity.opacity())
        self.toast_anim.setEndValue(0.0)
        self.toast_anim.start()

    def _on_toast_anim_finished(self) -> None:
        if self.toast_opacity.opacity() <= 0.05:
            self.toast_label.setVisible(False)

    def reposition(self, parent_width: int, parent_height: int) -> None:
        """Centers the dock horizontally 20px above the bottom margin of the parent viewport."""
        self._update_dock_geometry()
        x = (parent_width - self.width()) // 2
        y = parent_height - self.height() - 20
        self.move(x, y)
        self.raise_()

    def set_theme_mode(self, theme_mode: Literal["dark", "light"]) -> None:
        """Propagates theme change across dock items, shadows, and popovers."""
        self.current_theme = theme_mode
        if theme_mode == "dark":
            self.shadow.setColor(QColor(0, 0, 0, 60))
        else:
            self.shadow.setColor(QColor(0, 0, 0, 20))

        theme_btn = self.buttons.get("theme_toggle")
        if theme_btn:
            new_tooltip = "Modo Claro" if theme_mode == "dark" else "Modo Escuro"
            theme_btn.config.tooltip_text = new_tooltip
            theme_btn.config.label = new_tooltip
            theme_btn.setToolTip(new_tooltip)

        for btn in self.buttons.values():
            btn.update_icon()

        if hasattr(self, "log_popover"):
            self.log_popover.set_theme_mode(theme_mode)
        if hasattr(self, "version_popover"):
            self.version_popover.set_theme_mode(theme_mode)

    # Popover & Action triggers
    def _on_theme_toggle_clicked(self) -> None:
        parent = self.parentWidget()
        if parent and hasattr(parent, "toggle_theme_mode"):
            parent.toggle_theme_mode()
        elif parent and hasattr(parent, "_toggle_theme"):
            parent._toggle_theme()

    def _on_event_log_clicked(self) -> None:
        btn = self.buttons.get("event_log")
        if btn:
            if self.log_popover.isVisible():
                self.log_popover.hide()
            else:
                self.log_popover.show_above_widget(btn)

    def _on_check_updates_clicked(self) -> None:
        # Delegate to main window if parent has check_for_updates
        parent = self.parentWidget()
        if parent and hasattr(parent, "check_for_updates"):
            parent.check_for_updates(silent=False)
        else:
            self.show_toast("Todas as dependências e o SyncFrame estão na versão mais recente")

    def _on_version_info_clicked(self) -> None:
        btn = self.buttons.get("version_info")
        if btn:
            if self.version_popover.isVisible():
                self.version_popover.hide()
            else:
                self.version_popover.show_above_widget(btn)

    # Forwarding / backwards-compatibility methods
    def append_log(self, message: str) -> None:
        """Forwards log message to EventLogPopover and updates event badge count."""
        self.log_popover.append_log(message)
        self.update_badge_count("event_log", self.log_popover.event_count)

    def clear_logs(self) -> None:
        """Clears logs in popover and resets badge."""
        self.log_popover.clear_logs()
        self.update_badge_count("event_log", 0)
