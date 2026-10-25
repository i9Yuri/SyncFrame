"""Inspection preview player and LipSyncController for spot-checking synchronized playback at key markers."""

import logging
import os
import shutil
from typing import Optional

from PySide6.QtCore import QObject, QProcess, Qt, Signal
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


class LipSyncController(QObject):
    """
    Deterministic controller managing synchronized multimedia playback via QProcess.
    Invocates mpv (with transparent ffplay fallback), injecting compensated --audio-delay.
    """

    playback_state_changed = Signal(bool)
    timecode_updated = Signal(str)
    status_changed = Signal(str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.video_path: Optional[str] = None
        self.audio_path: Optional[str] = None
        self.total_duration_sec: float = 0.0
        self.active_process: Optional[QProcess] = None

    def set_media(
        self,
        video_path: Optional[str],
        audio_path: Optional[str],
        duration_sec: float = 0.0
    ) -> None:
        """Sets source media paths and duration."""
        self.video_path = video_path
        self.audio_path = audio_path
        self.total_duration_sec = duration_sec

    def play_marker(self, marker_percent: int, offset_ms: float = 0.0) -> bool:
        """
        Launches playback at the nominal marker percentage (5%, 50%, 90%)
        with acoustic offset delay applied. Forcefully terminates any active process first.
        """
        if not self.video_path or not os.path.exists(self.video_path):
            self.status_changed.emit("Erro: Arquivo de vídeo indisponível")
            return False

        has_mpv = shutil.which("mpv") is not None
        has_ffplay = shutil.which("ffplay") is not None

        if not has_mpv and not has_ffplay:
            self.status_changed.emit("Erro: mpv e ffplay não encontrados no sistema")
            return False

        # Terminate any previously running process compulsory
        self.stop_playback()

        pct_val = int(marker_percent if marker_percent > 1 else round(marker_percent * 100))
        pct_float = pct_val / 100.0

        start_sec = max(0.0, self.total_duration_sec * pct_float)
        hh = int(start_sec // 3600)
        mm = int((start_sec % 3600) // 60)
        ss = start_sec % 60
        tc_str = f"{hh:02d}:{mm:02d}:{ss:06.3f}"
        self.timecode_updated.emit(tc_str)

        delay_sec = map_offset_to_player_delay(offset_ms, "mpv" if has_mpv else "ffplay")
        self.status_changed.emit(f"Reproduzindo trecho aos {pct_val}%... (delay: {delay_sec:+.3f}s)")

        if has_mpv:
            prog = "mpv"
            args = [
                f"--start={start_sec:.2f}",
                "--length=12",
                f"--audio-delay={delay_sec:.4f}",
                "--force-window=yes",
                "--title=SyncFrame — Lip-Sync Spot Check"
            ]
            if self.audio_path and os.path.exists(self.audio_path) and self.audio_path != self.video_path:
                args.append(f"--audio-file={self.audio_path}")
            args.append(self.video_path)
        else:
            prog = "ffplay"
            args = [
                "-ss", f"{start_sec:.2f}",
                "-t", "12",
                "-window_title", "SyncFrame — Lip-Sync Spot Check",
                "-autoexit"
            ]
            delay_ms_int = int(round(delay_sec * 1000.0))
            if delay_ms_int != 0:
                args.extend(["-af", f"adelay={delay_ms_int}|{delay_ms_int}"])
            args.append(self.video_path)

        try:
            self.active_process = QProcess(self)
            self.active_process.finished.connect(self._on_finished)
            self.active_process.errorOccurred.connect(self._on_error)
            self.active_process.start(prog, args)
            self.playback_state_changed.emit(True)
            return True
        except Exception as exc:
            logger.error("Falha ao invocar %s: %s", prog, exc)
            self.status_changed.emit(f"Falha ao iniciar {prog}: {exc}")
            self.playback_state_changed.emit(False)
            return False

    def stop_playback(self) -> None:
        """Forcefully terminates the active playback process (SIGTERM/kill) and resets state."""
        if self.active_process is not None:
            if self.active_process.state() != QProcess.NotRunning:
                self.active_process.kill()
                self.active_process.waitForFinished(400)
            self.active_process = None
        self.playback_state_changed.emit(False)
        self.status_changed.emit("Pronto para reprodução sincronizada nos marcadores")

    def _on_finished(self, exit_code: int, exit_status):
        self.active_process = None
        self.playback_state_changed.emit(False)
        self.status_changed.emit("Pronto para reprodução sincronizada nos marcadores")

    def _on_error(self, error):
        logger.warning("Erro no processo de preview: %s", error)
        self.active_process = None
        self.playback_state_changed.emit(False)


class PreviewPlayer(QFrame):
    """
    Mini inspection preview runner styled as a One UI technical monitor with timecode overlay
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

        self.controller = LipSyncController(self)
        self.init_ui()
        self._wire_controller_signals()

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
        badge_backend.setFixedHeight(34)
        badge_backend.setAlignment(Qt.AlignCenter)
        header.addWidget(badge_backend)

        self.btn_stop = QPushButton("Parar")
        self.btn_stop.setObjectName("btnStopPreview")
        self.btn_stop.setProperty("class", "pill")
        self.btn_stop.setFixedHeight(34)
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_preview)
        header.addWidget(self.btn_stop)

        layout.addLayout(header)

        # Monitor visor display
        self.monitor_screen = QFrame()
        self.monitor_screen.setObjectName("monitorScreen")
        self.monitor_screen.setProperty("class", "viewBox")
        self.monitor_screen.setMinimumHeight(160)
        ms_layout = QVBoxLayout(self.monitor_screen)
        ms_layout.setContentsMargins(16, 12, 16, 12)
        ms_layout.setSpacing(6)

        overlay_row = QHBoxLayout()
        overlay_row.addStretch()
        self.lbl_timecode = QLabel("00:00:00.000")
        self.lbl_timecode.setObjectName("lblTimecodeChip")
        self.lbl_timecode.setProperty("class", "tc")
        self.lbl_timecode.setFixedHeight(26)
        self.lbl_timecode.setAlignment(Qt.AlignCenter)
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
        self.btn_p05.setObjectName("btnMarkerP05")
        self.btn_p05.setProperty("class", "markerBtn")
        self.btn_p05.setFixedHeight(40)
        self.btn_p05.setCursor(Qt.PointingHandCursor)
        self.btn_p05.clicked.connect(lambda: self.play_marker(5))
        marker_row.addWidget(self.btn_p05)

        self.btn_p50 = QPushButton("50% · Meio")
        self.btn_p50.setObjectName("btnMarkerP50")
        self.btn_p50.setProperty("class", "markerBtn")
        self.btn_p50.setFixedHeight(40)
        self.btn_p50.setCursor(Qt.PointingHandCursor)
        self.btn_p50.clicked.connect(lambda: self.play_marker(50))
        marker_row.addWidget(self.btn_p50)

        self.btn_p90 = QPushButton("90% · Ato final")
        self.btn_p90.setObjectName("btnMarkerP90")
        self.btn_p90.setProperty("class", "markerBtn")
        self.btn_p90.setFixedHeight(40)
        self.btn_p90.setCursor(Qt.PointingHandCursor)
        self.btn_p90.clicked.connect(lambda: self.play_marker(90))
        marker_row.addWidget(self.btn_p90)

        # Aliases for backwards compatibility with tests and controller
        self.btn_m5 = self.btn_p05
        self.btn_m50 = self.btn_p50
        self.btn_m90 = self.btn_p90

        layout.addLayout(marker_row)

    def _wire_controller_signals(self):
        self.controller.playback_state_changed.connect(self.btn_stop.setEnabled)
        self.controller.timecode_updated.connect(self.lbl_timecode.setText)
        self.controller.status_changed.connect(self.status_label.setText)

    def set_media_sources(
        self,
        video_path: Optional[str],
        audio_path: Optional[str],
        duration_sec: float = 0.0,
        offset_ms: float = 0.0
    ):
        self.video_path = video_path
        self.audio_path = audio_path
        self.total_duration_sec = duration_sec
        self.current_offset_ms = offset_ms
        self.controller.set_media(video_path, audio_path, duration_sec)

        if video_path:
            self.status_label.setText(f"Pronto: {os.path.basename(video_path)}")
            self.set_markers_enabled(True)
        else:
            self.status_label.setText("Pronto para reprodução sincronizada nos marcadores")
            self.set_markers_enabled(False)

    def set_preview_ready(self, message: str = "") -> None:
        """Sets preview status message and enables marker buttons."""
        if message:
            self.status_label.setText(message)
        self.set_markers_enabled(True)

    def update_offset(self, offset_ms: float):
        self.current_offset_ms = offset_ms

    def set_markers_enabled(self, enabled: bool):
        self.btn_p05.setEnabled(enabled)
        self.btn_p50.setEnabled(enabled)
        self.btn_p90.setEnabled(enabled)

    def play_marker(self, percentage: float) -> bool:
        """Plays segment at marker percentage, highlighting active pill and updating progress bar."""
        pct_val = int(percentage if percentage > 1 else round(percentage * 100))
        self.playback_bar.setValue(pct_val)

        # Highlight active button
        self.btn_p05.setProperty("on", pct_val == 5)
        self.btn_p50.setProperty("on", pct_val == 50)
        self.btn_p90.setProperty("on", pct_val == 90)
        for b in [self.btn_p05, self.btn_p50, self.btn_p90]:
            b.style().unpolish(b)
            b.style().polish(b)

        return self.controller.play_marker(pct_val, self.current_offset_ms)

    def stop_preview(self):
        """Stops active playback."""
        self.controller.stop_playback()
        self.btn_p05.setProperty("on", False)
        self.btn_p50.setProperty("on", False)
        self.btn_p90.setProperty("on", False)
        for b in [self.btn_p05, self.btn_p50, self.btn_p90]:
            b.style().unpolish(b)
            b.style().polish(b)
