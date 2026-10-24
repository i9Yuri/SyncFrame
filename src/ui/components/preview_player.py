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
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget
)

from ...core.correlator import map_offset_to_player_delay

logger = logging.getLogger(__name__)


class PreviewPlayer(QFrame):
    """
    Mini inspection preview runner styled as a One UI 8.5 technical monitor with timecode overlay
    and fast marker selector buttons (05% Abertura, 50% Meio, 90% Ato final).
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("bentoCard")
        self.setProperty("class", "card")

        self.video_path: Optional[str] = None
        self.audio_path: Optional[str] = None
        self.total_duration_sec: float = 0.0
        self.current_offset_ms: float = 0.0
        self.active_proc: Optional[subprocess.Popen] = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(18, 16, 18, 16)

        # Header with Title and Tags
        header = QHBoxLayout()
        header.setSpacing(10)

        self.idx_badge = QLabel("03B")
        self.idx_badge.setVisible(False)
        header.addWidget(self.idx_badge)

        title = QLabel("Teste de lip-sync")
        title.setProperty("class", "cardHeaderTitle")
        header.addWidget(title)
        header.addStretch()

        badge_backend = QLabel("Backend MPV")
        badge_backend.setObjectName("badgeBackendMpv")
        badge_backend.setProperty("class", "pillSoft")
        header.addWidget(badge_backend)

        self.btn_stop = QPushButton("Parar")
        self.btn_stop.setObjectName("btnStopPreview")
        self.btn_stop.setProperty("class", "pill")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_preview)
        header.addWidget(self.btn_stop)

        layout.addLayout(header)

        # Monitor visor display (Full Width, 160px height, #0c0d10 background)
        self.monitor_screen = QFrame()
        self.monitor_screen.setProperty("class", "viewBox")
        self.monitor_screen.setMinimumHeight(160)
        ms_layout = QVBoxLayout(self.monitor_screen)
        ms_layout.setContentsMargins(16, 12, 16, 12)
        ms_layout.setSpacing(6)

        # Top line: timecode chip in upper right
        overlay_row = QHBoxLayout()
        overlay_row.addStretch()
        self.lbl_timecode = QLabel("00:00:00.000")
        self.lbl_timecode.setObjectName("lblTimecodeChip")
        self.lbl_timecode.setProperty("class", "tc")
        overlay_row.addWidget(self.lbl_timecode)
        ms_layout.addLayout(overlay_row)

        ms_layout.addStretch()

        # Bottom: 6px capsule progress bar + status text
        self.playback_bar = QProgressBar()
        self.playback_bar.setObjectName("playbackBar")
        self.playback_bar.setRange(0, 100)
        self.playback_bar.setValue(0)
        self.playback_bar.setTextVisible(False)
        self.playback_bar.setFixedHeight(6)
        ms_layout.addWidget(self.playback_bar)

        self.status_label = QLabel("Pronto para reprodução sincronizada nos marcadores")
        self.status_label.setObjectName("lblPlayerStatus")
        self.status_label.setProperty("class", "hint")
        ms_layout.addWidget(self.status_label)

        layout.addWidget(self.monitor_screen)

        # Horizontal Marker Selector Row (3 buttons side-by-side)
        marker_row = QHBoxLayout()
        marker_row.setSpacing(8)

        self.btn_p05 = QPushButton("5% · Abertura")
        self.btn_p05.setProperty("class", "markerBtn")
        self.btn_p05.clicked.connect(lambda: self.play_marker(0.05))
        marker_row.addWidget(self.btn_p05)

        self.btn_p50 = QPushButton("50% · Meio")
        self.btn_p50.setProperty("class", "markerBtn")
        self.btn_p50.clicked.connect(lambda: self.play_marker(0.50))
        marker_row.addWidget(self.btn_p50)

        self.btn_p90 = QPushButton("90% · Ato final")
        self.btn_p90.setProperty("class", "markerBtn")
        self.btn_p90.clicked.connect(lambda: self.play_marker(0.90))
        marker_row.addWidget(self.btn_p90)

        layout.addLayout(marker_row)

    def set_media_sources(self, video_path: Optional[str], audio_path: Optional[str], duration_sec: float = 0.0, offset_ms: float = 0.0):
        self.video_path = video_path
        self.audio_path = audio_path
        self.total_duration_sec = duration_sec
        self.current_offset_ms = offset_ms
        if video_path:
            self.status_label.setText(f"Pronto: {os.path.basename(video_path)}")
            self.set_markers_enabled(True)
        else:
            self.status_label.setText("Pronto para reprodução sincronizada nos marcadores")
            self.set_markers_enabled(False)

    def update_offset(self, offset_ms: float):
        self.current_offset_ms = offset_ms

    def set_markers_enabled(self, enabled: bool):
        self.btn_p05.setEnabled(enabled)
        self.btn_p50.setEnabled(enabled)
        self.btn_p90.setEnabled(enabled)

    def play_marker(self, percentage: float):
        if not self.video_path or not os.path.exists(self.video_path):
            self.status_label.setText("Erro: Arquivo de vídeo indisponível")
            return

        has_mpv = shutil.which("mpv") is not None
        has_ffplay = shutil.which("ffplay") is not None

        if not has_mpv and not has_ffplay:
            self.status_label.setText("Erro: mpv e ffplay não encontrados no sistema")
            return

        self.stop_preview()

        # Highlight active button
        self.btn_p05.setProperty("on", percentage == 0.05)
        self.btn_p50.setProperty("on", percentage == 0.50)
        self.btn_p90.setProperty("on", percentage == 0.90)
        for b in [self.btn_p05, self.btn_p50, self.btn_p90]:
            b.style().unpolish(b)
            b.style().polish(b)

        pct_val = int(percentage * 100)
        self.playback_bar.setValue(pct_val)

        start_sec = max(0.0, self.total_duration_sec * percentage)
        hh = int(start_sec // 3600)
        mm = int((start_sec % 3600) // 60)
        ss = start_sec % 60
        tc_str = f"{hh:02d}:{mm:02d}:{ss:06.3f}"
        self.lbl_timecode.setText(tc_str)

        delay_sec = map_offset_to_player_delay(self.current_offset_ms)
        self.status_label.setText(f"Reproduzindo em {pct_val}%… (delay: {delay_sec:+.3f}s)")

        if has_mpv:
            cmd = [
                "mpv",
                f"--start={start_sec:.2f}",
                "--length=12",
                f"--audio-delay={delay_sec:.4f}",
                "--force-window=yes",
                "--title=SyncFrame — Lip-Sync Spot Check"
            ]
            if self.audio_path and os.path.exists(self.audio_path) and self.audio_path != self.video_path:
                cmd.append(f"--audio-file={self.audio_path}")
            cmd.append(self.video_path)
            player_name = "MPV"
        else:
            cmd = [
                "ffplay",
                "-ss", f"{start_sec:.2f}",
                "-t", "12",
                "-window_title", "SyncFrame — Lip-Sync Spot Check",
                "-autoexit"
            ]
            delay_ms_int = int(round(delay_sec * 1000.0))
            if delay_ms_int != 0:
                cmd.extend(["-af", f"adelay={delay_ms_int}|{delay_ms_int}"])
            cmd.append(self.video_path)
            player_name = "ffplay"

        try:
            self.active_proc = subprocess.Popen(cmd)
            self.btn_stop.setEnabled(True)
        except Exception as e:
            logger.error("Falha ao invocar %s: %s", player_name, e)
            self.status_label.setText(f"Falha ao iniciar {player_name}: {e}")

    def stop_preview(self):
        if self.active_proc and self.active_proc.poll() is None:
            self.active_proc.terminate()
            self.active_proc = None
        self.btn_stop.setEnabled(False)
        self.status_label.setText("Pronto para reprodução sincronizada nos marcadores")
