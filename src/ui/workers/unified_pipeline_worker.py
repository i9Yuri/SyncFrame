"""Unified single-action pipeline worker executing extraction, FFT correlation, and lossless remux."""

import logging
import os
import threading
import traceback
from typing import Optional

from PySide6.QtCore import QThread, Signal

from ...core.correlator import compute_acoustic_correlation
from ...core.extractor import extract_reference_channel
from ...core.models import RemuxJob, SyncMetrics
from ...core.remuxer import execute_lossless_remux
from ...core.temp_manager import TempWorkspace

logger = logging.getLogger(__name__)


class UnifiedPipelineWorker(QThread):
    """
    Background worker orchestrating the continuous, autonomous single-action pipeline:
    1. Selective extraction of acoustic reference channels (-threads 2).
    2. FFT acoustic cross-correlation and signed offset calculation.
    3. Seamless transition into lossless remuxing (mkvmerge).
    """
    progress = Signal(float, str)
    metrics_ready = Signal(SyncMetrics)
    completed = Signal(bool, str)
    error = Signal(str)

    def __init__(self, job: RemuxJob, manual_offset_override: Optional[float] = None):
        super().__init__()
        self.job = job
        self.manual_offset_override = manual_offset_override
        self._cancel_event = threading.Event()

    def cancel(self):
        """Signals graceful cancellation to all active child steps."""
        self._cancel_event.set()

    def run(self):
        try:
            # Set worker thread priority lower (nice) where supported to prevent CPU starvation
            try:
                os.nice(5)
            except Exception:
                pass

            if self._cancel_event.is_set():
                self.completed.emit(False, "Operação cancelada pelo usuário.")
                return

            with TempWorkspace(session_name="unified_staging") as workspace:
                # Step 1: Acoustic Correlation (unless manual override is provided)
                if self.manual_offset_override is not None:
                    self.job.offset_ms = self.manual_offset_override
                    self.progress.emit(25.0, f"Utilizando offset manual informado ({self.job.offset_ms:+.1f} ms)...")
                else:
                    self.progress.emit(5.0, "Extraindo canal de áudio de referência (PCM 16kHz)...")
                    ref_wav = workspace.get_path("ref_sample.wav")
                    extract_reference_channel(
                        file_path=self.job.video_file,
                        stream_id=self.job.ref_audio_track_id,
                        duration_sec=120.0,
                        start_sec=15.0,
                        output_path=ref_wav,
                        apply_bandpass=True
                    )

                    if self._cancel_event.is_set():
                        self.completed.emit(False, "Operação cancelada.")
                        return

                    self.progress.emit(15.0, "Extraindo canal de áudio dublado para correlação acústica...")
                    target_wav = workspace.get_path("target_sample.wav")
                    extract_reference_channel(
                        file_path=self.job.target_audio_file,
                        stream_id=self.job.target_track_id,
                        duration_sec=120.0,
                        start_sec=15.0,
                        output_path=target_wav,
                        apply_bandpass=True
                    )

                    if self._cancel_event.is_set():
                        self.completed.emit(False, "Operação cancelada.")
                        return

                    self.progress.emit(25.0, "Calculando correlação espectral FFT e alinhamento acústico...")
                    metrics = compute_acoustic_correlation(ref_wav, target_wav, search_window_sec=120)
                    self.metrics_ready.emit(metrics)

                    if metrics.confidence_score < 0.30:
                        logger.warning("Low correlation confidence (%.2f). Using 0.0ms fallback.", metrics.confidence_score)
                        self.job.offset_ms = 0.0
                        self.progress.emit(35.0, "Pico de correlação com baixa confiança (<30%). Aplicando offset neutro de 0 ms...")
                    else:
                        self.job.offset_ms = metrics.static_offset_ms
                        self.progress.emit(
                            35.0,
                            f"Offset acústico determinado: {self.job.offset_ms:+.1f} ms (confiança: {metrics.confidence_score*100:.0f}%)..."
                        )

                if self._cancel_event.is_set():
                    self.completed.emit(False, "Operação cancelada.")
                    return

                # Step 2: Lossless Remux via mkvmerge
                def _remux_progress(pct: float, msg: str):
                    if pct >= 0:
                        # Scale progress from 35% to 100%
                        scaled = 35.0 + (pct * 0.65)
                        self.progress.emit(scaled, msg)
                    else:
                        self.progress.emit(-1.0, msg)

                self.progress.emit(40.0, "Iniciando multiplexação lossless com mkvmerge...")
                success = execute_lossless_remux(
                    job=self.job,
                    on_progress=_remux_progress,
                    cancel_event=self._cancel_event
                )

                if success:
                    self.progress.emit(100.0, "Sincronização e remux concluídos com sucesso!")
                    self.completed.emit(True, f"Arquivo sincronizado gerado com sucesso em:\n{self.job.output_path}")
                else:
                    self.completed.emit(False, "Multiplexação interrompida ou cancelada.")

        except Exception as exc:
            logger.error("UnifiedPipelineWorker failed: %s\n%s", exc, traceback.format_exc())
            self.error.emit(str(exc))
