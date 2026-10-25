"""Pre-flight modal dialog requesting permission and installing missing system dependencies."""

import logging
import os
import shutil
from typing import List, Optional

from PySide6.QtCore import QProcess, Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget
)

from ...utils.system_check import PreFlightChecker, PreFlightReport

logger = logging.getLogger(__name__)


class PreFlightDialog(QDialog):
    """
    Modal dialog displayed before main window startup when mandatory system dependencies are missing.
    Offers automatic guided installation via pkexec / dnf or graceful application exit.
    """

    def __init__(self, report: PreFlightReport, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.report = report
        self.install_process: Optional[QProcess] = None
        self.package_names = PreFlightChecker.get_package_names(report.missing_tools)

        self.setWindowTitle("SyncFrame — Diagnóstico de Dependências")
        self.setFixedSize(560, 360)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)

        # Card Container (28px continuous rounded corners)
        card = QFrame(self)
        card.setObjectName("preflightCard")
        card.setStyleSheet("""
            QFrame#preflightCard {
                background-color: #16171a;
                border: 1px solid #23252a;
                border-radius: 28px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # Title
        title_label = QLabel("Dependências do Sistema Necessárias")
        title_label.setStyleSheet("color: #f2f3f7; font-size: 18px; font-weight: 700;")
        layout.addWidget(title_label)

        # Descriptive text
        tools_str = ", ".join(self.report.missing_tools)
        pkgs_str = " ".join(self.package_names)

        desc_text = (
            f"O SyncFrame requer dependências de sistema para operar: <b>{tools_str}</b>.<br><br>"
            "Deseja autorizar a instalação automática via gerenciador de pacotes do sistema?"
        )
        self.lbl_description = QLabel(desc_text)
        self.lbl_description.setWordWrap(True)
        self.lbl_description.setStyleSheet("color: #9a9eac; font-size: 13px; line-height: 1.4;")
        layout.addWidget(self.lbl_description)

        # Terminal command info container
        cmd_box = QFrame()
        cmd_box.setStyleSheet("""
            QFrame {
                background-color: #1b1c20;
                border: 1px solid #26272d;
                border-radius: 14px;
                padding: 10px 14px;
            }
        """)
        cb_layout = QVBoxLayout(cmd_box)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_cmd = QLabel(f"Comando: sudo dnf install -y {pkgs_str}")
        self.lbl_cmd.setStyleSheet("color: #d1d4dc; font-family: monospace; font-size: 12px;")
        cb_layout.addWidget(self.lbl_cmd)
        layout.addWidget(cmd_box)

        layout.addStretch()

        # Status and progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate spinner
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #26272d;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #f2f3f7;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("color: #9a9eac; font-size: 12px;")
        layout.addWidget(self.lbl_status)

        # Action Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        self.btn_exit = QPushButton("Sair")
        self.btn_exit.setFixedHeight(34)
        self.btn_exit.setStyleSheet("""
            QPushButton {
                background-color: #26272d;
                color: #f2f3f7;
                border-radius: 17px;
                padding: 0 20px;
                font-weight: 600;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover {
                background-color: #33343b;
            }
        """)
        self.btn_exit.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_exit)

        self.btn_install = QPushButton("Instalar Dependências")
        self.btn_install.setFixedHeight(34)
        self.btn_install.setStyleSheet("""
            QPushButton {
                background-color: #f2f3f7;
                color: #121316;
                border-radius: 17px;
                padding: 0 20px;
                font-weight: 600;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover {
                background-color: #ffffff;
            }
            QPushButton:disabled {
                background-color: #33343b;
                color: #6a7080;
            }
        """)
        self.btn_install.clicked.connect(self.start_installation)
        btn_row.addWidget(self.btn_install)

        layout.addLayout(btn_row)
        root_layout.addWidget(card)

    def start_installation(self):
        """Invokes distribution package manager via pkexec supervisor."""
        self.btn_install.setEnabled(False)
        self.btn_exit.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.lbl_status.setText("Aguardando confirmação de privilégios de sistema...")

        cmd_prog = ""
        args: List[str] = []

        if shutil.which("pkexec"):
            cmd_prog = "pkexec"
            if shutil.which("dnf"):
                args = ["dnf", "install", "-y"] + self.package_names
            elif shutil.which("apt-get"):
                args = ["apt-get", "install", "-y"] + self.package_names
            elif shutil.which("pacman"):
                args = ["pacman", "-S", "--noconfirm"] + self.package_names
            else:
                args = ["dnf", "install", "-y"] + self.package_names
        else:
            self._on_process_finished(1, None)
            return

        self.install_process = QProcess(self)
        self.install_process.finished.connect(self._on_process_finished)
        self.install_process.start(cmd_prog, args)

    def _on_process_finished(self, exit_code: int, exit_status):
        self.progress_bar.setVisible(False)
        self.btn_exit.setEnabled(True)
        self.btn_install.setEnabled(True)

        if exit_code == 0:
            # Recheck dependencies
            new_report = PreFlightChecker.verify_system_binaries()
            if new_report.is_ready:
                self.lbl_status.setText("Todas as dependências foram instaladas com sucesso.")
                self.accept()
                return

        # Installation was rejected or failed
        pkgs_str = " ".join(self.package_names)
        self.lbl_status.setText(
            "A autorização foi recusada ou a instalação falhou.\n"
            f"Você pode instalar manualmente no terminal: sudo dnf install -y {pkgs_str}"
        )
