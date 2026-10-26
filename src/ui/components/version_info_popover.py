"""Version and diagnostic popover dialog showing system and engine status."""

import platform
import os
from typing import Dict, Literal, Optional

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class VersionInfoPopover(QWidget):
    """
    Floating popover displaying SyncFrame release version, execution environment, and media engine status.
    Adheres to continuous rounded geometry (pill chips) and clean monochromatic design.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setObjectName("versionInfoPopover")
        self.setFixedSize(400, 240)

        self.current_theme: Literal["dark", "light"] = "dark"
        self.app_version: str = "v1.5.0"
        self.tool_versions: Dict[str, str] = {}

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
        self.container.setObjectName("versionInfoPopoverContainer")

        # Elevation shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(24)
        self.shadow.setOffset(0, 6)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.container.setGraphicsEffect(self.shadow)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        header.setSpacing(10)
        self.lbl_title = QLabel("Diagnóstico do Sistema")
        self.lbl_title.setObjectName("popoverTitle")
        self.lbl_title.setProperty("class", "logTitle")
        header.addWidget(self.lbl_title)
        header.addStretch()

        self.chip_app_v = QLabel(f"SyncFrame {self.app_version}")
        self.chip_app_v.setObjectName("chipAppVersion")
        self.chip_app_v.setProperty("class", "systemChip")
        self.chip_app_v.setFixedHeight(28)
        self.chip_app_v.setAlignment(Qt.AlignCenter)
        header.addWidget(self.chip_app_v)
        layout.addLayout(header)

        # Information cards / chips list
        info_list = QVBoxLayout()
        info_list.setSpacing(8)

        # OS Environment Tag
        self.frame_os = QFrame()
        self.frame_os.setProperty("class", "pill")
        self.frame_os.setFixedHeight(34)
        os_layout = QHBoxLayout(self.frame_os)
        os_layout.setContentsMargins(12, 0, 12, 0)
        os_layout.setSpacing(8)
        lbl_os_prefix = QLabel("Ambiente:")
        lbl_os_prefix.setStyleSheet("font-weight: 600; font-size: 11px;")
        os_layout.addWidget(lbl_os_prefix)
        self.lbl_os_val = QLabel(self._detect_os_string())
        self.lbl_os_val.setStyleSheet("font-size: 11px;")
        os_layout.addWidget(self.lbl_os_val, 1)
        info_list.addWidget(self.frame_os)

        # Media Engines Tag
        self.frame_engines = QFrame()
        self.frame_engines.setProperty("class", "pill")
        self.frame_engines.setFixedHeight(34)
        eng_layout = QHBoxLayout(self.frame_engines)
        eng_layout.setContentsMargins(12, 0, 12, 0)
        eng_layout.setSpacing(8)
        lbl_eng_prefix = QLabel("Motores:")
        lbl_eng_prefix.setStyleSheet("font-weight: 600; font-size: 11px;")
        eng_layout.addWidget(lbl_eng_prefix)
        self.lbl_engines_val = QLabel("FFmpeg • MKVToolNix • MPV")
        self.lbl_engines_val.setStyleSheet("font-size: 11px;")
        eng_layout.addWidget(self.lbl_engines_val, 1)
        info_list.addWidget(self.frame_engines)

        # Status row
        self.frame_status = QFrame()
        self.frame_status.setProperty("class", "pillSoft")
        self.frame_status.setFixedHeight(34)
        st_layout = QHBoxLayout(self.frame_status)
        st_layout.setContentsMargins(12, 0, 12, 0)
        st_layout.setSpacing(8)
        self.dot_status = QLabel()
        self.dot_status.setProperty("class", "greenDot")
        self.dot_status.setFixedSize(8, 8)
        st_layout.addWidget(self.dot_status)
        self.lbl_status_text = QLabel("Todas as ferramentas operacionais")
        self.lbl_status_text.setStyleSheet("font-size: 11px; font-weight: 600;")
        st_layout.addWidget(self.lbl_status_text, 1)
        info_list.addWidget(self.frame_status)

        layout.addLayout(info_list)
        root_layout.addWidget(self.container)

    def _detect_os_string(self) -> str:
        """Extracts clean OS name and architecture without bloated paths."""
        # Check /etc/os-release if on Linux
        if os.path.isfile("/etc/os-release"):
            try:
                with open("/etc/os-release", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            val = line.split("=", 1)[1].strip()
                            pretty = val.replace('"', '').replace("'", '')
                            return f"{pretty} ({platform.machine()})"
            except Exception:
                pass
        return f"{platform.system()} {platform.release()} ({platform.machine()})"

    def set_system_info(self, app_version: str, tool_versions: Dict[str, str]) -> None:
        """Updates version badges and engine statuses."""
        if app_version:
            self.app_version = app_version
            self.chip_app_v.setText(f"SyncFrame {app_version}")
        if tool_versions:
            self.tool_versions = tool_versions
            parts = []
            for tool in ["ffmpeg", "mkvmerge", "mpv"]:
                ver = tool_versions.get(tool, "Detectado")
                # Format concisely
                display_name = "FFmpeg" if tool == "ffmpeg" else ("MKVToolNix" if tool == "mkvmerge" else "MPV")
                if ver and ver != "Detectado":
                    parts.append(f"{display_name} {ver}")
                else:
                    parts.append(display_name)
            if parts:
                self.lbl_engines_val.setText(" • ".join(parts))

    def set_theme_mode(self, theme_mode: Literal["dark", "light"]) -> None:
        """Adjusts shadow and colors for theme."""
        self.current_theme = theme_mode
        if theme_mode == "dark":
            self.shadow.setColor(QColor(0, 0, 0, 80))
        else:
            self.shadow.setColor(QColor(0, 0, 0, 30))

    def show_above_widget(self, target: QWidget) -> None:
        """Positions the popover centered horizontally above the target widget with a 14px gap, clamped to screen bounds."""
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
