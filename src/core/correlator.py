"""Acoustic correlation engine using Pearson/FFT cross-correlation and multi-window drift analysis."""

import logging
import math
import wave
from typing import Callable, List, Optional, Tuple

import numpy as np

try:
    from scipy import signal as scipy_signal
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

from .models import SyncMetrics
from .temp_manager import TempWorkspace

logger = logging.getLogger(__name__)

# Known framerate ratio signatures and diagnoses
KNOWN_RATIOS = [
    (1001.0 / 1000.0, "23.976 fps -> 24.000 fps (NTSC telecine drift ~ +0.1001%)"),
    (1000.0 / 1001.0, "24.000 fps -> 23.976 fps (NTSC telecine drift ~ -0.0999%)"),
    (25.0 / 24.0, "24.000 fps -> 25.000 fps (PAL Speedup ~ +4.167%)"),
    (24.0 / 25.0, "25.000 fps -> 24.000 fps (PAL Slowdown ~ -4.000%)"),
    (25.0 / (24000.0 / 1001.0), "23.976 fps -> 25.000 fps (NTSC -> PAL Speedup ~ +4.271%)"),
    ((24000.0 / 1001.0) / 25.0, "25.000 fps -> 23.976 fps (PAL -> NTSC Slowdown ~ -4.096%)"),
]


def load_wav_mono(file_path: str, max_duration_sec: Optional[float] = None) -> Tuple[np.ndarray, int]:
    """
    Reads a 16-bit PCM mono WAV file into a normalized float32 numpy array.
    Applies streaming chunking/capping to strictly prevent RAM exhaustion on long media files.
    """
    # Safe guard: cap at 600 seconds (10 minutes) maximum if unconstrained to protect RAM
    effective_max_sec = max_duration_sec if (max_duration_sec and max_duration_sec > 0) else 600.0

    with wave.open(file_path, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()

        if effective_max_sec:
            n_frames = min(n_frames, int(effective_max_sec * framerate))

        raw_bytes = wf.readframes(n_frames)

    if sampwidth == 2:
        samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 1:
        samples = (np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    elif sampwidth == 4:
        samples = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"Unsupported WAV sample width: {sampwidth} bytes")

    if n_channels > 1:
        # Downmix if multi-channel
        samples = samples.reshape(-1, n_channels).mean(axis=1)

    return samples, framerate


def _cross_correlate_fft(x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes cross-correlation R_xy[k] = sum(x[n] * y[n - k]) using FFT.
    Returns:
        (lags, normalized_correlation)
    """
    nx = len(x)
    ny = len(y)
    if nx == 0 or ny == 0:
        return np.array([0]), np.array([0.0])

    # Zero-mean normalization for Pearson correlation
    x_centered = x - np.mean(x)
    y_centered = y - np.mean(y)

    norm_x = np.linalg.norm(x_centered)
    norm_y = np.linalg.norm(y_centered)
    denominator = norm_x * norm_y

    if denominator <= 1e-12:
        return np.arange(-ny + 1, nx), np.zeros(nx + ny - 1, dtype=np.float32)

    if HAS_SCIPY:
        corr = scipy_signal.correlate(y_centered, x_centered, mode="full", method="fft")
        lags = scipy_signal.correlation_lags(ny, nx, mode="full")
    else:
        # Cross-correlation R_yx[k] = (y * x_rev)[k]
        out_len = ny + nx - 1
        n_fft = 1 << (out_len - 1).bit_length()
        fy = np.fft.rfft(y_centered, n_fft)
        fx_rev = np.fft.rfft(x_centered[::-1], n_fft)
        corr_full = np.fft.irfft(fy * fx_rev, n_fft)
        corr = corr_full[:out_len]
        lags = np.arange(-nx + 1, ny)

    norm_corr = (corr / denominator).astype(np.float32)
    return lags, norm_corr


def calculate_signed_offset(
    ref_signal: np.ndarray,
    target_signal: np.ndarray,
    sample_rate: int,
    max_lag_sec: float = 60.0
) -> float:
    """
    Calcula o offset temporal estritamente assinado entre o sinal de referência e o sinal alvo.
    
    Contrato Matemático:
    - Se o áudio dublado (alvo) inicia DEPOIS da referência (atrasado):
      retorna valor POSITIVO (+ms). Necessita de adiantamento / delay negativo no contêiner.
    - Se o áudio dublado (alvo) inicia ANTES da referência (adiantado):
      retorna valor NEGATIVO (-ms). Necessita de injeção de delay positivo no contêiner.
    """
    offset_ms, _, _ = calculate_offset_from_signals(
        ref_signal, target_signal, sample_rate, max_lag_sec=max_lag_sec
    )
    return float(offset_ms)


def map_offset_to_player_delay(
    offset_ms: float,
    player_engine: str
) -> float:
    """
    Converte deterministicamente o offset calculado para o atraso/adiantamento
    exigido por cada motor de reprodução ou remux.
    
    Regras de sinal:
    - 'mkvmerge': Retorna o valor em milissegundos para a flag --sync 0:<delay>.
      Áudio dublado atrasado (+ms) requer delay negativo no contêiner para adiantamento.
      Retorna: -float(offset_ms)
      
    - 'mpv': Retorna o valor em segundos para a flag --audio-delay=<sec>.
      Em mpv, valores positivos atrasam o áudio e negativos atrasam o vídeo / adiantam o áudio.
      Para sincronizar áudio dublado atrasado (+ms), adianta-se o áudio (-segundos).
      Retorna: -(float(offset_ms) / 1000.0)
      
    - 'ffplay': Retorna o valor em segundos para compensação temporal.
      Retorna: -(float(offset_ms) / 1000.0)
    """
    engine = player_engine.lower()
    if engine == "mkvmerge":
        return -float(offset_ms)
    elif engine in ("mpv", "ffplay"):
        return -(float(offset_ms) / 1000.0)
    else:
        raise ValueError(f"Motor de player/remux desconhecido: '{player_engine}'")


def calculate_offset_from_signals(
    ref_sig: np.ndarray,
    target_sig: np.ndarray,
    sample_rate: int,
    max_lag_sec: float = 60.0
) -> Tuple[float, float, List[float]]:
    """
    Finds the relative time offset between reference and target audio signals.
    A positive offset means target is delayed relative to reference.
    
    Returns:
        (offset_ms, confidence_score, preview_curve)
    """
    lags, corr = _cross_correlate_fft(ref_sig, target_sig)

    # Restrict lag search to within max_lag_sec
    max_lag_samples = int(max_lag_sec * sample_rate)
    valid_mask = (lags >= -max_lag_samples) & (lags <= max_lag_samples)

    if not np.any(valid_mask):
        return 0.0, 0.0, []

    valid_lags = lags[valid_mask]
    valid_corr = corr[valid_mask]

    peak_idx = int(np.argmax(valid_corr))
    peak_val = float(valid_corr[peak_idx])
    best_lag_samples = int(valid_lags[peak_idx])

    # Convert lag to milliseconds (positive lag => target audio is delayed relative to ref)
    offset_ms = (best_lag_samples / float(sample_rate)) * 1000.0

    # Calculate confidence: Blend of normalized absolute peak value and peak prominence SNR
    raw_peak = float(np.clip(peak_val, 0.0, 1.0))
    std_corr = float(np.std(valid_corr))
    mean_corr = float(np.mean(valid_corr))
    peak_prominence = max(0.0, (peak_val - mean_corr) / (std_corr + 1e-9))

    conf_prom = float(np.clip(peak_prominence / 4.0, 0.0, 1.0))
    confidence = float(0.5 * raw_peak + 0.5 * conf_prom)

    # Downsample correlation peak neighborhood for UI preview curve (~100 points)
    window_half = min(len(valid_corr) // 2, int(0.5 * sample_rate))  # 500ms window
    left_bound = max(0, peak_idx - window_half)
    right_bound = min(len(valid_corr), peak_idx + window_half)
    peak_neighborhood = valid_corr[left_bound:right_bound]

    step = max(1, len(peak_neighborhood) // 100)
    preview_curve = [float(val) for val in peak_neighborhood[::step]]

    return offset_ms, confidence, preview_curve


def compute_acoustic_correlation(
    ref_wav: str,
    target_wav: str,
    search_window_sec: int = 180
) -> SyncMetrics:
    """
    Computes single-window acoustic correlation between two pre-extracted WAV files.
    """
    ref_sig, sr_ref = load_wav_mono(ref_wav, max_duration_sec=search_window_sec)
    target_sig, sr_tgt = load_wav_mono(target_wav, max_duration_sec=search_window_sec)

    if sr_ref != sr_tgt:
        raise ValueError(f"Sample rates do not match: {sr_ref}Hz vs {sr_tgt}Hz")

    offset_ms, confidence, preview = calculate_offset_from_signals(
        ref_sig, target_sig, sr_ref, max_lag_sec=60.0
    )

    return SyncMetrics(
        static_offset_ms=offset_ms,
        drift_ratio=1.0,
        confidence_score=confidence,
        detected_fps_mismatch=False,
        time_stretch_ratio=1.0,
        fps_diagnosis="Offset estático calculado em janela única",
        offsets_by_window=[(0.0, offset_ms, confidence)],
        correlation_curve=preview
    )


def diagnose_drift_and_framerate(
    offsets_by_time: List[Tuple[float, float, float]]
) -> Tuple[float, bool, str, float]:
    """
    Analyzes temporal offsets measured across time windows to detect continuous drift
    and map it to standard framerate conversion discrepancies.

    Args:
        offsets_by_time: List of (timestamp_sec, offset_ms, confidence)

    Returns:
        (drift_ratio, detected_fps_mismatch, fps_diagnosis, time_stretch_ratio)
    """
    # Filter only reliable window measurements (confidence >= 0.25)
    valid_points = [p for p in offsets_by_time if p[2] >= 0.25]

    if len(valid_points) < 2:
        return 1.0, False, "Pontos insuficientes para cálculo de deriva contínua", 1.0

    times = np.array([p[0] for p in valid_points], dtype=np.float64)
    offsets = np.array([p[1] for p in valid_points], dtype=np.float64)

    # Linear regression: offset_ms(t) = a * t_sec + b
    # slope 'a' has units of ms_drift / sec_time
    if len(times) >= 2:
        slope, intercept = np.polyfit(times, offsets, 1)
    else:
        slope = 0.0

    # Drift ratio: 1.0 + (slope in seconds / sec) = 1.0 + (slope / 1000.0)
    drift_ratio = float(1.0 + (slope / 1000.0))

    # If drift is under 150 parts per million (~0.5s over 1 hour), it is considered congruous
    if abs(drift_ratio - 1.0) < 0.00015:
        return 1.0, False, "Taxas de quadros congruentes (sem deriva contínua)", 1.0

    # Match against known standard framerate discrepancy ratios
    detected_mismatch = True
    diagnosis = f"Deriva linear contínua detectada: {drift_ratio:.6f}"
    closest_ratio_diff = 1.0
    best_diagnosis = diagnosis

    for ratio, desc in KNOWN_RATIOS:
        diff = abs(drift_ratio - ratio)
        if diff < 0.0008 and diff < closest_ratio_diff:
            closest_ratio_diff = diff
            best_diagnosis = f"Discrepância detectada: {desc} (Razão: {drift_ratio:.6f})"

    # Time stretch required to compress or expand audio to match video duration:
    # stretch_ratio = 1.0 / drift_ratio
    time_stretch_ratio = float(1.0 / drift_ratio)

    return drift_ratio, detected_mismatch, best_diagnosis, time_stretch_ratio
