"""Harmonized, zero-latency completion modal for SyncFrame."""

import logging
import os
import shutil
import subprocess
import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget
)

logger = logging.getLogger(__name__)


def get_runtime_resource_path(relative_path: str) -> str:
    """
    Resolves the absolute path to a resource, supporting both development mode
    and PyInstaller bundled execution via sys._MEIPASS.
    """
    base_path = getattr(
        sys,
        "_MEIPASS",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    )
    return os.path.normpath(os.path.join(base_path, relative_path))


def open_containing_folder(file_path: str) -> bool:
    """
    Opens the containing directory in the host file manager (e.g. Dolphin, Nautilus, xdg-open)
    and highlights the target file if supported, without freezing the GUI thread.
    Returns True if successfully launched, False otherwise.
    """
    if not file_path:
        return False

    try:
        abs_path = os.path.abspath(file_path)
        folder_path = os.path.dirname(abs_path) if os.path.isfile(abs_path) else abs_path
        if not os.path.exists(folder_path):
            folder_path = os.path.expanduser("~")

        # Prioritize KDE Dolphin with file selection
        if shutil.which("dolphin") and os.path.isfile(abs_path):
            subprocess.Popen(["dolphin", "--select", abs_path])
            return True
        # Prioritize GNOME Nautilus with file selection
        elif shutil.which("nautilus") and os.path.isfile(abs_path):
            subprocess.Popen(["nautilus", "--select", abs_path])
            return True
        # Generic freedesktop file manager via xdg-open
        elif shutil.which("xdg-open"):
            subprocess.Popen(["xdg-open", folder_path])
            return True
        else:
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices
            return QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))
    except Exception as exc:
        logger.warning("Could not open containing folder for %s: %s", file_path, exc)
        return False


class CompletionDialog(QDialog):
    """
    Lightweight, instant-mounting modal dialog reporting completion.
    Adheres strictly to the neutral monochromatic design system without
    animations, blur, or rendering overhead.
    """

    def __init__(self, output_file_path: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.output_file_path = output_file_path or ""
        self.setObjectName("completionDialog")
        self.setWindowTitle("Processo Concluído — SyncFrame")
        self.setModal(True)
        self.setFixedSize(540, 240)
        self.setStyleSheet("""
            QDialog#completionDialog {
                background-color: #1b1c20;
                color: #f2f3f7;
                border-radius: 28px;
                border: 1px solid #33343b;
            }
            QLabel#badgeSuccessGlyph {
                border-radius: 18px;
                background-color: rgba(47, 177, 107, 0.16);
                color: #2fb16b;
                font-weight: 700;
                font-size: 13px;
            }
            QLineEdit#outputBoxMonospace {
                background-color: #26272d;
                color: #f2f3f7;
                border: 1px solid #33343b;
                border-radius: 17px;
                height: 34px;
                min-height: 34px;
                max-height: 34px;
                /* border-radius: 999px; */
                padding: 0 14px;
                font-family: monospace;
            }
        """)

        self._init_ui()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(22, 20, 22, 20)
        root_layout.setSpacing(14)

        # Header with discrete confirmation glyph and technical text
        header_row = QHBoxLayout()
        header_row.setSpacing(14)
        header_row.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.glyph_badge = QLabel("OK")
        self.glyph_badge.setObjectName("badgeSuccessGlyph")
        self.glyph_badge.setAlignment(Qt.AlignCenter)
        self.glyph_badge.setFixedSize(36, 36)
        header_row.addWidget(self.glyph_badge)

        header_text_box = QVBoxLayout()
        header_text_box.setSpacing(3)

        title = QLabel("Processo Concluído")
        title.setObjectName("completionTitle")
        title.setProperty("class", "cardTitle")
        header_text_box.addWidget(title)

        subtitle = QLabel("O arquivo sincronizado foi gerado com êxito e multiplexado sem perdas.")
        subtitle.setProperty("class", "subText")
        header_text_box.addWidget(subtitle)

        header_row.addLayout(header_text_box)
        header_row.addStretch()

        badge_audit = QLabel("AUDITADO EM MALHA FECHADA")
        badge_audit.setProperty("class", "badgeGreen")
        header_row.addWidget(badge_audit)

        root_layout.addLayout(header_row)

        # Delimited monospace path display
        path_box = QVBoxLayout()
        path_box.setSpacing(6)

        lbl_path_desc = QLabel("Arquivo de Saída:")
        lbl_path_desc.setProperty("class", "subText")
        path_box.addWidget(lbl_path_desc)

        self.txt_path = QLineEdit(self.output_file_path)
        self.txt_path.setObjectName("outputBoxMonospace")
        self.txt_path.setReadOnly(True)
        self.txt_path.setCursorPosition(0)
        path_box.addWidget(self.txt_path)

        root_layout.addLayout(path_box)

        # Action Buttons Row
        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.btn_open_folder = QPushButton("Abrir Diretório")
        self.btn_open_folder.setObjectName("btnOpenFolder")
        self.btn_open_folder.setProperty("class", "btnSecondary")
        self.btn_open_folder.setCursor(Qt.PointingHandCursor)
        self.btn_open_folder.clicked.connect(self._on_open_folder_clicked)
        button_row.addWidget(self.btn_open_folder)

        button_row.addStretch()

        self.btn_close = QPushButton("OK / Fechar")
        self.btn_close.setObjectName("btnCloseCompletion")
        self.btn_close.setProperty("class", "btnPrimary")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setDefault(True)
        self.btn_close.setFocus()
        self.btn_close.clicked.connect(self.accept)
        button_row.addWidget(self.btn_close)

        root_layout.addLayout(button_row)

    def _on_open_folder_clicked(self):
        """Attempts to open directory in file manager; falls back to copying to clipboard."""
        success = open_containing_folder(self.output_file_path)
        if success:
            self.btn_open_folder.setText("Pasta Aberta")
        else:
            clipboard = QApplication.clipboard()
            if clipboard and self.output_file_path:
                clipboard.setText(self.output_file_path)
            self.btn_open_folder.setText("Caminho Copiado!")

    def keyPressEvent(self, event):
        """Keyboard ergonomics: closes immediately on Escape or Enter."""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape):
            self.accept()
        else:
            super().keyPressEvent(event)


def show_completion_modal(parent: Optional[QWidget], output_file_path: str) -> None:
    """
    Displays the styled, zero-latency completion modal dialog.
    """
    dialog = CompletionDialog(output_file_path=output_file_path, parent=parent)
    dialog.exec()
