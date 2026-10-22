"""Background QThread worker for acoustic feature extraction and FFT correlation."""

import logging
import traceback
from typing import List, Optional, Tuple

from PySide6.QtCore import QThread, Signal

from ...core.correlator import (
    calculate_offset_from_signals,
    diagnose_drift_and_framerate,
    load_wav_mono
)
from ...core.extractor import extract_reference_channel
from ...core.models import SyncMetrics
from ...core.temp_manager import TempWorkspace

logger = logging.getLogger(__name__)


class AnalyzeWorker(QThread):
    """
    Asynchronously extracts mono PCM samples and computes FFT cross-correlation
    across 3 temporal windows (5%, 50%, 85%) to detect static offset and continuous drift.
    """
    progress = Signal(float, str)
    finished = Signal(SyncMetrics)
    error = Signal(str)

    def __init__(
        self,
        video_path: str,
        video_audio_track_id: int,
        audio_path: str,
        target_audio_track_id: int,
        duration_sec: float
    ):
        super().__init__()
        self.video_path = video_path
        self.video_audio_track_id = video_audio_track_id
        self.audio_path = audio_path
        self.target_audio_track_id = target_audio_track_id
        self.duration_sec = max(30.0, duration_sec)
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

    def run(self):
        try:
            with TempWorkspace(session_name="analyze_staging") as staging:
                self.progress.emit(5.0, "Iniciando staging para análise espectral...")

                # Define window positions: 5%, 50%, 85%
                window_duration = min(180.0, max(20.0, self.duration_sec * 0.05))
                window_pcts = [0.05, 0.50, 0.85]
                window_results: List[Tuple[float, float, float]] = []
                primary_preview_curve: List[float] = []

                step_pct = 85.0 / (len(window_pcts) * 2)
                curr_progress = 10.0

                for i, pct in enumerate(window_pcts):
                    if self.is_cancelled:
                        return

                    start_sec = max(0.0, (self.duration_sec * pct) - (window_duration / 2.0))
                    pct_int = int(pct * 100)

                    # Extract reference audio window
                    self.progress.emit(
                        curr_progress,
                        f"Extraindo amostras acústicas da janela {pct_int}% (ref)..."
                    )
                    ref_wav = staging.get_path(f"ref_w{i}_{int(start_sec)}.wav")
                    extract_reference_channel(
                        file_path=self.video_path,
                        stream_id=self.video_audio_track_id,
                        target_sr=16000,
                        duration_sec=window_duration,
                        start_sec=start_sec,
                        output_path=ref_wav,
                        apply_bandpass=True
                    )
                    curr_progress += step_pct

                    if self.is_cancelled:
                        return

                    # Extract target dubbed audio window
                    self.progress.emit(
                        curr_progress,
                        f"Extraindo amostras acústicas da janela {pct_int}% (dublado)..."
                    )
                    tgt_wav = staging.get_path(f"tgt_w{i}_{int(start_sec)}.wav")
                    extract_reference_channel(
                        file_path=self.audio_path,
                        stream_id=self.target_audio_track_id,
                        target_sr=16000,
                        duration_sec=window_duration,
                        start_sec=start_sec,
                        output_path=tgt_wav,
                        apply_bandpass=True
                    )
                    curr_progress += step_pct

                    # Load mono signals and correlate
                    ref_sig, sr_ref = load_wav_mono(ref_wav)
                    tgt_sig, sr_tgt = load_wav_mono(tgt_wav)

                    offset_ms, conf, curve = calculate_offset_from_signals(
                        ref_sig, tgt_sig, sr_ref, max_lag_sec=60.0
                    )
                    window_results.append((start_sec, offset_ms, conf))

                    if i == 0 or (conf > 0.4 and not primary_preview_curve):
                        primary_preview_curve = curve

                # Analyze drift and framerate mismatch
                self.progress.emit(90.0, "Diagnosticando deriva contínua e divergência de framerate...")
                drift_ratio, detected_mismatch, diagnosis, stretch_ratio = diagnose_drift_and_framerate(
                    window_results
                )

                # Use initial window or most confident window for static initial offset
                valid_windows = [w for w in window_results if w[2] >= 0.25]
                if valid_windows:
                    static_offset = valid_windows[0][1]
                    avg_conf = sum(w[2] for w in valid_windows) / len(valid_windows)
                else:
                    static_offset = window_results[0][1]
                    avg_conf = window_results[0][2]

                metrics = SyncMetrics(
                    static_offset_ms=static_offset,
                    drift_ratio=drift_ratio,
                    confidence_score=avg_conf,
                    detected_fps_mismatch=detected_mismatch,
                    time_stretch_ratio=stretch_ratio,
                    fps_diagnosis=diagnosis,
                    offsets_by_window=window_results,
                    correlation_curve=primary_preview_curve
                )

                self.progress.emit(100.0, "Análise de sincronização concluída!")
                self.finished.emit(metrics)

        except Exception as exc:
            logger.error("AnalyzeWorker failed: %s\n%s", exc, traceback.format_exc())
            self.error.emit(str(exc))
