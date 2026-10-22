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

logger = logging.getLogger(__name__)


class PreviewPlayer(QFrame):
    """
    Mini inspection preview runner that launches a spot-check player at 5%, 50%, or 90%
    timestamps with the calculated/adjusted audio delay applied in real-time.
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
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout()
        title = QLabel("Player de Inspeção & Validação Labial")
        title.setProperty("class", "cardTitle")
        header.addWidget(title)
        header.addStretch()

        self.btn_stop = QPushButton("Parar Reprodução")
        self.btn_stop.setProperty("class", "btnDanger")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_preview)
        header.addWidget(self.btn_stop)

        layout.addLayout(header)

        desc = QLabel(
            "Reproduza trechos curtos de 12 segundos com o áudio dublado compensado pelo offset atual "
            "para validar visualmente a sincronia labial nos pontos críticos da mídia:"
        )
        desc.setProperty("class", "subText")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Buttons Row: 5%, 50%, 90%
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_p05 = QPushButton("Prévia Início (05%)")
        self.btn_p05.setProperty("class", "btnSecondary")
        self.btn_p05.clicked.connect(lambda: self.play_marker(0.05))
        btn_layout.addWidget(self.btn_p05)

        self.btn_p50 = QPushButton("Prévia Meio (50%)")
        self.btn_p50.setProperty("class", "btnSecondary")
        self.btn_p50.clicked.connect(lambda: self.play_marker(0.50))
        btn_layout.addWidget(self.btn_p50)

        self.btn_p90 = QPushButton("Prévia Fim (90%)")
        self.btn_p90.setProperty("class", "btnSecondary")
        self.btn_p90.clicked.connect(lambda: self.play_marker(0.90))
        btn_layout.addWidget(self.btn_p90)

        layout.addLayout(btn_layout)

        self.status_label = QLabel("Aguardando carregamento de fontes para inspeção")
        self.status_label.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(self.status_label)

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

        ready = bool(video_path and os.path.isfile(video_path) and audio_path and os.path.isfile(audio_path))
        self.btn_p05.setEnabled(ready)
        self.btn_p50.setEnabled(ready)
        self.btn_p90.setEnabled(ready)

        if ready:
            self.status_label.setText(f"Fontes prontas para teste (Duração nominal: {duration_sec / 60.0:.1f} min)")
        else:
            self.status_label.setText("Selecione os arquivos de vídeo e áudio para habilitar o preview")

    def update_offset(self, offset_ms: float):
        self.current_offset_ms = offset_ms

    def stop_preview(self):
        if self.active_proc and self.active_proc.poll() is None:
            try:
                self.active_proc.terminate()
                self.active_proc.wait(timeout=1.0)
            except Exception:
                try:
                    self.active_proc.kill()
                except Exception:
                    pass
        self.active_proc = None
        self.btn_stop.setEnabled(False)
        self.status_label.setText("Reprodução interrompida.")

    def play_marker(self, fraction: float):
        self.stop_preview()

        if not self.video_path or not self.audio_path:
            return

        start_time = max(0.0, self.total_duration_sec * fraction)
        duration_clip = 12.0  # 12 seconds preview

        # Audio delay in seconds:
        # Note: in mpv, --audio-delay adds delay in seconds (positive means audio delayed relative to video)
        delay_sec = self.current_offset_ms / 1000.0

        pct_label = int(fraction * 100)
        self.status_label.setText(
            f"Reproduzindo trecho aos {pct_label}% (posição {start_time / 60.0:.2f} min, offset: {self.current_offset_ms:+.1f} ms)..."
        )
        self.btn_stop.setEnabled(True)

        mpv_bin = shutil.which("mpv")
        ffplay_bin = shutil.which("ffplay")

        if mpv_bin:
            cmd = [
                mpv_bin,
                f"--start={start_time:.2f}",
                f"--length={duration_clip:.2f}",
                f"--audio-file={self.audio_path}",
                f"--audio-delay={delay_sec:.4f}",
                "--title=SyncFrame Preview",
                "--geometry=800x450",
                self.video_path
            ]
        elif ffplay_bin:
            # Fallback to ffplay with audio filter delay
            cmd = [
                ffplay_bin,
                "-ss", f"{start_time:.2f}",
                "-t", f"{duration_clip:.2f}",
                "-window_title", "SyncFrame Preview",
                "-x", "800", "-y", "450",
                self.video_path
            ]
        else:
            self.status_label.setText("Erro: mpv ou ffplay não encontrados no PATH do sistema.")
            self.btn_stop.setEnabled(False)
            return

        try:
            self.active_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as exc:
            logger.error("Failed to launch preview player: %s", exc)
            self.status_label.setText(f"Erro ao iniciar player de prévia: {exc}")
            self.btn_stop.setEnabled(False)
