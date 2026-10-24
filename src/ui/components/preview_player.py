"""Inspection preview player for spot-checking synchronized playback at key markers."""

import logging
import os
import shutil
import subprocess
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget
)

from ...core.correlator import map_offset_to_player_delay

logger = logging.getLogger(__name__)


class PreviewPlayer(QFrame):
    """
    Mini inspection preview runner styled as a technical monitor with timecode overlay
    and fast marker selector buttons (05% Opening, 50% Midpoint, 90% Final Act).
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("bentoCard")
        self.setProperty("class", "bentoCard")

        self.video_path: Optional[str] = None
        self.audio_path: Optional[str] = None
        self.total_duration_sec: float = 0.0
        self.current_offset_ms: float = 0.0
        self.active_proc: Optional[subprocess.Popen] = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 16, 18, 16)

        # Header with Title and Section Index
        header = QHBoxLayout()
        header.setSpacing(8)

        idx_badge = QLabel("03B")
        idx_badge.setProperty("class", "sectionIndex")
        header.addWidget(idx_badge)

        title = QLabel("Lip-Sync Spot Check & Player")
        title.setProperty("class", "cardTitle")
        header.addWidget(title)
        header.addStretch()

        badge_backend = QLabel("MPV BACKEND")
        badge_backend.setProperty("class", "badgeNeutral")
        header.addWidget(badge_backend)

        self.btn_stop = QPushButton("Parar")
        self.btn_stop.setProperty("class", "btnDanger")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_preview)
        header.addWidget(self.btn_stop)

        layout.addLayout(header)

        # Monitor visor display & markers layout
        mid_row = QHBoxLayout()
        mid_row.setSpacing(12)

        # Screen Monitor Frame
        self.monitor_screen = QFrame()
        self.monitor_screen.setProperty("class", "viewportScreen")
        self.monitor_screen.setMinimumHeight(84)
        ms_layout = QVBoxLayout(self.monitor_screen)
        ms_layout.setContentsMargins(12, 10, 12, 10)

        overlay_row = QHBoxLayout()
        lbl_screen_tag = QLabel("VISOR DE SINAL")
        lbl_screen_tag.setProperty("class", "eyebrowText")
        lbl_screen_tag.setStyleSheet("background: transparent; color: #7e8792; font-size: 10px; font-weight: 600; letter-spacing: 1px; border: none;")
        overlay_row.addWidget(lbl_screen_tag)
        overlay_row.addStretch()
        self.lbl_timecode = QLabel("00:00:00.000")
        self.lbl_timecode.setObjectName("lblTimecodeChip")
        self.lbl_timecode.setProperty("class", "timecodeChip")
        overlay_row.addWidget(self.lbl_timecode)
        ms_layout.addLayout(overlay_row)

        ms_layout.addStretch()
        self.status_label = QLabel("Aguardando carregamento de fontes para inspeção")
        self.status_label.setStyleSheet("background: transparent; color: #a8a8a8; font-size: 11px; border: none;")
        ms_layout.addWidget(self.status_label)
        mid_row.addWidget(self.monitor_screen, 1)

        # Vertical Marker Selector Stack
        marker_stack = QVBoxLayout()
        marker_stack.setSpacing(6)

        self.btn_p05 = QPushButton("05% Opening")
        self.btn_p05.setProperty("class", "markerBtn")
        self.btn_p05.clicked.connect(lambda: self.play_marker(0.05))
        marker_stack.addWidget(self.btn_p05)

        self.btn_p50 = QPushButton("50% Midpoint")
        self.btn_p50.setProperty("class", "markerBtn")
        self.btn_p50.clicked.connect(lambda: self.play_marker(0.50))
        marker_stack.addWidget(self.btn_p50)

        self.btn_p90 = QPushButton("90% Final Act")
        self.btn_p90.setProperty("class", "markerBtn")
        self.btn_p90.clicked.connect(lambda: self.play_marker(0.90))
        marker_stack.addWidget(self.btn_p90)

        mid_row.addLayout(marker_stack)
        layout.addLayout(mid_row)

    def _set_status(self, text: str, color: str = "#a8a8a8", bold: bool = False):
        weight = "700" if bold else "400"
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            f"background: transparent; color: {color}; font-size: 11px; font-weight: {weight}; border: none;"
        )

    def set_media_sources(
        self,
        video_path: Optional[str],
        audio_path: Optional[str],
        duration_sec: float,
        offset_ms: float
    ):
        self.video_path = video_path
        self.audio_path = audio_path
        self.total_duration_sec = duration_sec
        self.current_offset_ms = offset_ms

        if self.video_path and self.audio_path:
            self._set_status("Pronto para reprodução sincronizada nos marcadores", color="#ffffff", bold=True)
        else:
            self._set_status("Aguardando carregamento de fontes para inspeção", color="#a8a8a8")

    def update_offset(self, offset_ms: float):
        self.current_offset_ms = offset_ms

    def play_marker(self, fraction: float):
        if not self.video_path or not self.audio_path:
            self._set_status("Fontes de mídia não carregadas.", color="#ffffff")
            return

        self.stop_preview()

        start_time = max(0.0, self.total_duration_sec * fraction)

        # Format timecode (hh:mm:ss.zzz)
        hours = int(start_time // 3600)
        minutes = int((start_time % 3600) // 60)
        seconds = start_time % 60
        self.lbl_timecode.setText(f"{hours:02d}:{minutes:02d}:{seconds:06.3f}")

        player_delay_sec = map_offset_to_player_delay(self.current_offset_ms)

        player_bin = shutil.which("mpv")
        if not player_bin:
            self._set_status("mpv não instalado no sistema.", color="#ffffff")
            return

        cmd = [
            player_bin,
            self.video_path,
            f"--audio-file={self.audio_path}",
            f"--audio-delay={player_delay_sec:.4f}",
            f"--start={start_time:.2f}",
            "--length=12",
            "--title=SyncFrame — Lip-Sync Inspection",
            "--keep-open=no",
            "--no-terminal",
            "--geometry=854x480-20+40"
        ]

        try:
            self.active_proc = subprocess.Popen(cmd)
            self.btn_stop.setEnabled(True)
            self._set_active_marker_fraction(fraction)
            self._set_status(
                f"Reproduzindo trecho ({int(fraction * 100)}%) com delay de {player_delay_sec:+.3f}s",
                color="#ffffff"
            )
        except Exception as exc:
            logger.error("Failed to launch preview player: %s", exc)
            self._set_status(f"Erro ao iniciar player: {exc}", color="#ffffff")

    def _set_active_marker_fraction(self, fraction: Optional[float]):
        for btn, frac in [(self.btn_p05, 0.05), (self.btn_p50, 0.50), (self.btn_p90, 0.90)]:
            is_active = "true" if fraction is not None and abs(fraction - frac) < 0.01 else "false"
            btn.setProperty("active", is_active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def stop_preview(self):
        if self.active_proc and self.active_proc.poll() is None:
            try:
                self.active_proc.terminate()
            except Exception:
                pass
        self.active_proc = None
        self._set_active_marker_fraction(None)
        self.btn_stop.setEnabled(False)
        self._set_status("Reprodução encerrada.", color="#a8a8a8")
