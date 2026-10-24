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
    # Standard contract signals
    analysis_started = Signal()
    step_progress = Signal(str, float)  # (status_message, percentage_float)
    correlation_ready = Signal(dict)    # dict with offset_ms, confidence, pslr, curve_points
    correlation_completed = Signal(float, float, float, list)  # (offset_ms, confidence, drift_ratio, corr_curve)
    preview_ready = Signal(object)
    finished_success = Signal(str)     # output_path
    execution_failed = Signal(str)     # error_message

    # Backwards-compatibility signals
    progress = Signal(float, str)       # (percentage_float, status_message)
    metrics_ready = Signal(SyncMetrics)
    completed = Signal(bool, str)
    error = Signal(str)
    log_message = Signal(str)

    def __init__(
        self,
        job: RemuxJob,
        manual_offset_override: Optional[float] = None,
        parent: Optional[object] = None
    ):
        super().__init__(parent)
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
                self.execution_failed.emit("Operação cancelada pelo usuário.")
                return

            self.analysis_started.emit()
            self.step_progress.emit("Iniciando extração e análise acústica...", 5.0)
            self.progress.emit(5.0, "Iniciando extração e análise acústica...")
            self.log_message.emit("Iniciando esteira unificada de processamento...")

            with TempWorkspace(session_name="unified_staging") as workspace:
                # Step 1: Acoustic Correlation (unless manual override is provided)
                if self.manual_offset_override is not None:
                    self.job.offset_ms = self.manual_offset_override
                    msg = f"Utilizando offset manual informado ({self.job.offset_ms:+.1f} ms)..."
                    self.step_progress.emit(msg, 25.0)
                    self.progress.emit(25.0, msg)
                    self.log_message.emit(msg)
                else:
                    msg_ref = "Extraindo canal de áudio de referência (PCM 16kHz)..."
                    self.step_progress.emit(msg_ref, 10.0)
                    self.progress.emit(10.0, msg_ref)
                    self.log_message.emit(msg_ref)

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
                        self.execution_failed.emit("Operação cancelada.")
                        return

                    msg_tgt = "Extraindo canal de áudio dublado para correlação acústica..."
                    self.step_progress.emit(msg_tgt, 20.0)
                    self.progress.emit(20.0, msg_tgt)
                    self.log_message.emit(msg_tgt)

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
                        self.execution_failed.emit("Operação cancelada.")
                        return

                    msg_fft = "Calculando correlação espectral FFT e alinhamento acústico..."
                    self.step_progress.emit(msg_fft, 25.0)
                    self.progress.emit(25.0, msg_fft)
                    self.log_message.emit(msg_fft)

                    metrics = compute_acoustic_correlation(ref_wav, target_wav, search_window_sec=120)

                    # Emit correlation signals
                    corr_dict = {
                        "offset_ms": metrics.static_offset_ms,
                        "confidence": metrics.confidence_score,
                        "pslr": metrics.pslr_score,
                        "curve_points": list(metrics.correlation_curve)
                    }
                    self.correlation_ready.emit(corr_dict)
                    self.correlation_completed.emit(
                        metrics.static_offset_ms,
                        metrics.confidence_score,
                        metrics.drift_ratio,
                        list(metrics.correlation_curve)
                    )
                    self.metrics_ready.emit(metrics)
                    self.preview_ready.emit(corr_dict)

                    if metrics.confidence_score < 0.30:
                        logger.warning("Low correlation confidence (%.2f). Using 0.0ms fallback.", metrics.confidence_score)
                        self.job.offset_ms = 0.0
                        msg_low = "Pico de correlação com baixa confiança (<30%). Aplicando offset neutro de 0 ms..."
                        self.step_progress.emit(msg_low, 35.0)
                        self.progress.emit(35.0, msg_low)
                        self.log_message.emit(msg_low)
                    else:
                        self.job.offset_ms = metrics.static_offset_ms
                        msg_det = f"Offset acústico determinado: {self.job.offset_ms:+.1f} ms (confiança: {metrics.confidence_score*100:.0f}%)..."
                        self.step_progress.emit(msg_det, 35.0)
                        self.progress.emit(35.0, msg_det)
                        self.log_message.emit(msg_det)

                if self._cancel_event.is_set():
                    self.completed.emit(False, "Operação cancelada.")
                    self.execution_failed.emit("Operação cancelada.")
                    return

                # Step 2: Lossless Remux via mkvmerge
                def _remux_progress(pct: float, msg: str):
                    if pct >= 0:
                        scaled = 35.0 + (pct * 0.65)
                        self.step_progress.emit(msg, scaled)
                        self.progress.emit(scaled, msg)
                    else:
                        self.log_message.emit(msg)

                msg_remux = "Iniciando multiplexação lossless com mkvmerge..."
                self.step_progress.emit(msg_remux, 40.0)
                self.progress.emit(40.0, msg_remux)
                self.log_message.emit(msg_remux)

                success = execute_lossless_remux(
                    job=self.job,
                    on_progress=_remux_progress,
                    cancel_event=self._cancel_event
                )

                if success:
                    msg_done = "Sincronização e remux concluídos com sucesso!"
                    self.step_progress.emit(msg_done, 100.0)
                    self.progress.emit(100.0, msg_done)
                    self.log_message.emit(f"Arquivo gerado: {self.job.output_path}")
                    self.finished_success.emit(self.job.output_path)
                    self.completed.emit(True, f"Arquivo sincronizado gerado com sucesso em:\n{self.job.output_path}")
                else:
                    err = "Multiplexação interrompida ou cancelada."
                    self.execution_failed.emit(err)
                    self.completed.emit(False, err)

        except Exception as exc:
            err_msg = f"Falha na execução do pipeline: {exc}"
            logger.error("UnifiedPipelineWorker failed: %s\n%s", exc, traceback.format_exc())
            self.execution_failed.emit(err_msg)
            self.error.emit(str(exc))
            self.completed.emit(False, err_msg)


# Alias for contract compatibility
PipelineWorker = UnifiedPipelineWorker
