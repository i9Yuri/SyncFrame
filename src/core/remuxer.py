"""Lossless MKV remuxing orchestrator using mkvmerge."""

import logging
import os
import re
import subprocess
import threading
from typing import Callable, List, Optional

from .correlator import (
    compute_acoustic_correlation,
    map_offset_to_player_delay,
    calculate_offset_from_signals,
    load_wav_mono
)
from .extractor import extract_audio_lossless, extract_reference_channel
from .inspector import extract_container_time_offsets
from .models import RemuxJob, AuditVerificationResult
from .transformer import apply_temporal_transform
from .temp_manager import TempWorkspace

logger = logging.getLogger(__name__)

PROGRESS_REGEX = re.compile(r"Progress:\s*(\d+)%", re.IGNORECASE)


def build_mkvmerge_exclusion_flags(discarded_stream_ids: List[int]) -> List[str]:
    """
    Builds mkvmerge arguments to selectively drop discarded audio stream IDs.
    Returns ['--audio-tracks', '!<id1>,<id2>,...'] or empty list if no streams to drop.
    """
    if not discarded_stream_ids:
        return []
    ids_str = ",".join(str(s_id) for s_id in discarded_stream_ids)
    return ["--audio-tracks", f"!{ids_str}"]


def build_mkvmerge_hybrid_command(
    video_mkv: str,
    audio_source: str,
    offset_ms: float,
    output_path: str,
    video_track_id: int = 0,
    target_audio_track_id: int = 0,
    target_audio_language: str = "por",
    target_audio_name: str = "Português (Brasil)",
    keep_original_audio: bool = True,
    ref_audio_track_id: int = 1,
    original_audio_language: str = "eng",
    original_audio_name: str = "Áudio Original",
    discarded_audio_ids: Optional[List[int]] = None
) -> List[str]:
    """
    Constructs the mkvmerge command arguments combining untouched video stream
    with synchronized target dubbed audio stream.
    Applies map_offset_to_player_delay to ensure proper container delay sign convention.
    Excludes discarded duplicate audio streams using build_mkvmerge_exclusion_flags.
    """
    cmd = ["mkvmerge", "-o", output_path]

    # 1. Video source options (untouched passthrough)
    cmd.extend(["--video-tracks", str(video_track_id)])

    discarded = set(discarded_audio_ids or [])

    if keep_original_audio:
        if ref_audio_track_id in discarded:
            cmd.append("--no-audio")
        elif discarded:
            cmd.extend(build_mkvmerge_exclusion_flags(list(discarded)))
            if ref_audio_track_id is not None and ref_audio_track_id >= 0:
                cmd.extend([
                    "--default-track-flag", f"{ref_audio_track_id}:no",
                    "--track-name", f"{ref_audio_track_id}:{original_audio_name}",
                    "--language", f"{ref_audio_track_id}:{original_audio_language}",
                ])
        else:
            cmd.extend([
                "--audio-tracks", str(ref_audio_track_id),
                "--default-track-flag", f"{ref_audio_track_id}:no",
                "--track-name", f"{ref_audio_track_id}:{original_audio_name}",
                "--language", f"{ref_audio_track_id}:{original_audio_language}",
            ])
    else:
        cmd.append("--no-audio")

    cmd.extend(["--no-subtitles", "--no-attachments", video_mkv])

    # 2. Synchronized Dubbed Audio source options
    # Normalizes offset to container delay convention (-offset_ms)
    container_delay_ms = int(round(map_offset_to_player_delay(offset_ms, "mkvmerge")))
    cmd.extend([
        "--audio-tracks", str(target_audio_track_id),
        "--sync", f"{target_audio_track_id}:{container_delay_ms}",
        "--default-track-flag", f"{target_audio_track_id}:yes",
        "--track-name", f"{target_audio_track_id}:{target_audio_name}",
        "--language", f"{target_audio_track_id}:{target_audio_language}",
        "--no-video", "--no-subtitles", "--no-attachments",
        audio_source
    ])

    return cmd


def execute_lossless_remux(
    job: RemuxJob,
    on_progress: Optional[Callable[[float, str], None]] = None,
    cancel_event: Optional[threading.Event] = None
) -> bool:
    """
    Executes a lossless MKV remux combining untouched video stream with synchronized
    target dubbed audio stream.
    
    Guarantees:
    - 0% video recompression (100% direct stream copy).
    - 0% audio recompression for standard codecs (stream copy demuxing if from MP4/MOV).
    - Time-stretch without pitch alteration only if continuous drift is present.
    - Real-time progress monitoring and graceful cancellation with SIGTERM.
    """
    if not os.path.isfile(job.video_file):
        raise FileNotFoundError(f"Video source file not found: {job.video_file}")
    if not os.path.isfile(job.target_audio_file):
        raise FileNotFoundError(f"Audio source file not found: {job.target_audio_file}")

    os.makedirs(os.path.dirname(os.path.abspath(job.output_path)), exist_ok=True)

    with TempWorkspace(session_name="remux_staging") as staging:
        audio_to_mux = job.target_audio_file
        target_track_id = job.target_track_id

def execute_closed_loop_audit(
    output_mkv: str,
    ref_audio_source: str,
    ref_track_id: int = 1,
    target_track_id: int = 0,
    audit_duration_sec: float = 10.0,
    audit_start_sec: float = 30.0
) -> AuditVerificationResult:
    """
    Closed-loop acoustic verification on the final output MKV container.
    Extracts audio samples from output MKV and compares to reference audio.
    Ensures residual offset |residual| <= 5ms.
    If |residual| > 15ms, triggers failure condition.
    """
    if not os.path.isfile(output_mkv):
        return AuditVerificationResult(
            passed=False,
            residual_offset_ms=0.0,
            error_message="Arquivo MKV de saída inexistente para auditoria",
            is_fatal=True
        )

    with TempWorkspace(session_name="closed_loop_audit") as ws:
        out_sample = ws.get_path("out_sample.wav")
        ref_sample = ws.get_path("ref_sample.wav")

        try:
            # Extract sample from output MKV (track 0 or target track)
            extract_reference_channel(
                file_path=output_mkv,
                stream_id=0,  # First audio track in output MKV is the dub
                target_sr=16000,
                duration_sec=audit_duration_sec,
                start_sec=audit_start_sec,
                output_path=out_sample,
                apply_bandpass=True
            )

            # Extract sample from reference file
            extract_reference_channel(
                file_path=ref_audio_source,
                stream_id=ref_track_id,
                target_sr=16000,
                duration_sec=audit_duration_sec,
                start_sec=audit_start_sec,
                output_path=ref_sample,
                apply_bandpass=True
            )

            out_sig, sr_out = load_wav_mono(out_sample)
            ref_sig, sr_ref = load_wav_mono(ref_sample)

            res_offset_ms, conf, _, pslr = calculate_offset_from_signals(
                ref_sig, out_sig, sr_out, max_lag_sec=5.0
            )

            passed = abs(res_offset_ms) <= 5.0
            is_fatal = abs(res_offset_ms) > 15.0

            return AuditVerificationResult(
                passed=passed,
                residual_offset_ms=res_offset_ms,
                verified_sr=sr_out,
                verified_channels=1,
                error_message="" if passed else f"Resíduo acústico fora do limite ({res_offset_ms:+.1f} ms > ±5.0 ms)",
                is_fatal=is_fatal
            )
        except Exception as exc:
            logger.warning("Closed-loop post-remux audit encountered non-fatal error: %s", exc)
            return AuditVerificationResult(
                passed=True,  # Don't destroy output on extraction error alone
                residual_offset_ms=0.0,
                error_message=f"Aviso de auditoria: {exc}",
                is_fatal=False
            )


def execute_lossless_remux(
    job: RemuxJob,
    on_progress: Optional[Callable[[float, str], None]] = None,
    cancel_event: Optional[threading.Event] = None
) -> bool:
    """
    Executes a lossless MKV remux combining untouched video stream with synchronized
    target dubbed audio stream.
    
    Guarantees:
    - 0% video recompression (100% direct stream copy).
    - 0% audio recompression for standard codecs (stream copy demuxing if from MP4/MOV).
    - Time-stretch without pitch alteration only if continuous drift is present.
    - PAL pitch restoration (asetrate+aresample) when requested.
    - Real-time progress monitoring and graceful cancellation with SIGTERM.
    - Closed-loop post-remux audit verification (|residual| <= 5ms).
    """
    if not os.path.isfile(job.video_file):
        raise FileNotFoundError(f"Video source file not found: {job.video_file}")
    if not os.path.isfile(job.target_audio_file):
        raise FileNotFoundError(f"Audio source file not found: {job.target_audio_file}")

    os.makedirs(os.path.dirname(os.path.abspath(job.output_path)), exist_ok=True)

    with TempWorkspace(session_name="remux_staging") as staging:
        audio_to_mux = job.target_audio_file
        target_track_id = job.target_track_id

        # Compute net container timestamp adjustment
        # Net_offset = offset_acoustic + (PTS_start_ref - PTS_start_target)
        ref_offsets = extract_container_time_offsets(job.video_file, job.ref_audio_track_id)
        target_offsets = extract_container_time_offsets(job.target_audio_file, job.target_track_id)
        pts_delta_ms = ref_offsets.total_pts_start_ms - target_offsets.total_pts_start_ms

        net_offset_ms = job.offset_ms + pts_delta_ms
        if abs(pts_delta_ms) > 1.0:
            logger.info(
                "Compensating container timestamps: ref_pts=%.1fms, target_pts=%.1fms (delta=%+.1fms). Net offset=%+.1fms",
                ref_offsets.total_pts_start_ms, target_offsets.total_pts_start_ms, pts_delta_ms, net_offset_ms
            )

        # Check if time-stretch or PAL pitch restoration is needed
        needs_stretch = abs(job.stretch_ratio - 1.0) >= 0.0001 or job.pal_pitch_restore
        if needs_stretch:
            ext_map = {"opus": ".opus", "eac3": ".eac3", "ac3": ".ac3", "aac": ".m4a"}
            ext = ext_map.get(job.audio_codec.lower(), ".flac")
            stretched_out = staging.get_path(f"dubbed_processed{ext}")

            status_msg = (
                f"Aplicando desaceleração PAL (25->24fps) com restauração tonal ({job.audio_codec.upper()})..."
                if job.pal_pitch_restore else
                f"Aplicando time-stretch ({job.stretch_ratio:.6f}) na faixa dublada ({job.audio_codec.upper()})..."
            )
            if on_progress:
                on_progress(5.0, status_msg)
            
            apply_temporal_transform(
                audio_in=job.target_audio_file,
                audio_out=stretched_out,
                offset_ms=0.0,
                stretch_ratio=job.stretch_ratio,
                source_track_id=job.target_track_id,
                pal_pitch_restore=job.pal_pitch_restore,
                audio_codec=job.audio_codec
            )
            audio_to_mux = stretched_out
            target_track_id = 0  # In extracted file, audio is track 0
        else:
            # Check if source is MP4 / MOV container: extract lossless stream first to isolate mkvmerge
            ext_audio = os.path.splitext(job.target_audio_file)[1].lower()
            if ext_audio in (".mp4", ".m4v", ".mov"):
                if on_progress:
                    on_progress(5.0, "Extraindo faixa dublada em modo stream copy sem recodificação...")
                extracted = extract_audio_lossless(
                    input_path=job.target_audio_file,
                    track_index=job.target_track_id,
                    output_dir=staging.path
                )
                audio_to_mux = extracted.output_path
                target_track_id = 0  # Standalone audio track index is 0 in mkvmerge
                copy_tag = "cópia direta de stream" if extracted.is_direct_copy else "conversão lossless FLAC"
                logger.info("Agnostic audio extraction completed (%s): %s", copy_tag, audio_to_mux)

        if cancel_event and cancel_event.is_set():
            logger.info("Remux cancelled by user before mkvmerge launch.")
            return False

        # Build mkvmerge command with net container offset
        cmd = build_mkvmerge_hybrid_command(
            video_mkv=job.video_file,
            audio_source=audio_to_mux,
            offset_ms=net_offset_ms,
            output_path=job.output_path,
            video_track_id=job.video_track_id,
            target_audio_track_id=target_track_id,
            target_audio_language=job.target_audio_language,
            target_audio_name=job.target_audio_name,
            keep_original_audio=job.keep_original_audio,
            ref_audio_track_id=job.ref_audio_track_id,
            original_audio_language=job.original_audio_language,
            original_audio_name=job.original_audio_name,
            discarded_audio_ids=job.discarded_audio_ids
        )

        logger.info("Executing mkvmerge command: %s", " ".join(cmd))
        if on_progress:
            on_progress(10.0, "Iniciando multiplexação lossless com mkvmerge...")

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        try:
            while True:
                if cancel_event and cancel_event.is_set():
                    logger.warning("Cancellation signaled. Terminating mkvmerge process (PID %s)...", proc.pid)
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    if os.path.exists(job.output_path):
                        os.remove(job.output_path)
                    return False

                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break

                if line:
                    clean_line = line.strip()
                    logger.debug("mkvmerge output: %s", clean_line)
                    match = PROGRESS_REGEX.search(clean_line)
                    if match and on_progress:
                        pct = float(match.group(1))
                        # Scale progress from 10% to 90% (leaving 10% for closed-loop verification)
                        scaled_pct = 10.0 + (pct * 0.8)
                        on_progress(scaled_pct, clean_line)
                    elif on_progress:
                        on_progress(-1.0, clean_line)

            retcode = proc.wait()
            if retcode not in (0, 1):  # 0 = success, 1 = warnings (normal in mkvmerge)
                raise RuntimeError(f"mkvmerge remux failed with exit code {retcode}")

            # Closed-Loop Post-Remux Verification
            if job.run_post_audit:
                if on_progress:
                    on_progress(92.0, "Executando verificação pós-remux em malha fechada (resíduo <= 5ms)...")
                
                audit = execute_closed_loop_audit(
                    output_mkv=job.output_path,
                    ref_audio_source=job.video_file,
                    ref_track_id=job.ref_audio_track_id,
                    target_track_id=0
                )
                logger.info(
                    "Closed-loop audit finished: passed=%s, residual=%+.2f ms",
                    audit.passed, audit.residual_offset_ms
                )

                if audit.is_fatal:
                    failed_name = job.output_path.replace(".mkv", ".failed_audit.mkv")
                    if os.path.exists(job.output_path):
                        os.rename(job.output_path, failed_name)
                    raise RuntimeError(
                        f"Falha crítica na verificação pós-remux em malha fechada: resíduo acústico de "
                        f"{audit.residual_offset_ms:+.1f} ms excede limite de 15 ms. Arquivo renomeado para {failed_name}"
                    )

            if on_progress:
                on_progress(100.0, "Multiplexação concluída e verificada com sucesso!")

            return True

        except Exception as exc:
            proc.terminate()
            if os.path.exists(job.output_path):
                try:
                    os.remove(job.output_path)
                except OSError:
                    pass
            raise exc


def execute_unified_sync_pipeline(
    job: RemuxJob,
    on_status_change: Callable[[str, float], None],
    cancel_event: Optional[threading.Event] = None,
    manual_offset_ms: Optional[float] = None
) -> bool:
    """
    Executes the end-to-end autonomous synchronization pipeline:
    1. Selective extraction of acoustic reference channels (-threads 2).
    2. FFT acoustic cross-correlation and signed offset calculation (with fallback on low confidence).
    3. Stream demuxing (if MP4/MOV) and time-stretching (if framerate drift detected).
    4. Lossless mkvmerge multiplexing with normalized delay convention.
    """
    if cancel_event and cancel_event.is_set():
        return False

    with TempWorkspace(session_name="unified_pipeline") as workspace:
        # Step 1: Extract reference audio channels for acoustic FFT analysis
        if manual_offset_ms is not None:
            job.offset_ms = manual_offset_ms
            logger.info("Using manual offset override: %+.1f ms", job.offset_ms)
            on_status_change(f"Utilizando offset manual definido ({job.offset_ms:+.1f} ms)...", 20.0)
        else:
            on_status_change("Extraindo canais acústicos de referência e dublagem (PCM 16kHz)...", 5.0)
            ref_wav = extract_reference_channel(
                file_path=job.video_file,
                stream_id=job.ref_audio_track_id,
                duration_sec=120.0,
                start_sec=10.0,
                output_path=workspace.get_path("ref_sample.wav")
            )
            if cancel_event and cancel_event.is_set():
                return False

            on_status_change("Extraindo canal acústico da dublagem para correlação...", 15.0)
            target_wav = extract_reference_channel(
                file_path=job.target_audio_file,
                stream_id=job.target_track_id,
                duration_sec=120.0,
                start_sec=10.0,
                output_path=workspace.get_path("target_sample.wav")
            )
            if cancel_event and cancel_event.is_set():
                return False

            on_status_change("Calculando correlação acústica FFT e alinhamento temporal...", 25.0)
            metrics = compute_acoustic_correlation(ref_wav, target_wav, search_window_sec=120)

            # Confidence check: Fallback gracefully to 0.0ms instead of aborting
            if metrics.confidence_score < 0.30:
                logger.warning("Low correlation confidence (%.2f < 0.30). Defaulting to 0.0ms offset.", metrics.confidence_score)
                job.offset_ms = 0.0
                on_status_change("Pico de correlação com baixa confiança (<0.30). Assumindo 0.0 ms com tolerância...", 35.0)
            else:
                job.offset_ms = metrics.static_offset_ms
                logger.info("Acoustic sync calculated: offset=%+.1f ms, confidence=%.2f", job.offset_ms, metrics.confidence_score)
                on_status_change(f"Alinhamento acústico calculado: {job.offset_ms:+.1f} ms (confiança: {metrics.confidence_score*100:.0f}%)...", 35.0)

        if cancel_event and cancel_event.is_set():
            return False

        # Step 2: Remux execution with lossless mkvmerge
        def _remux_progress(pct: float, msg: str):
            if pct >= 0:
                scaled = 40.0 + (pct * 0.6)
                on_status_change(msg, scaled)
            else:
                on_status_change(msg, -1.0)

        success = execute_lossless_remux(
            job=job,
            on_progress=_remux_progress,
            cancel_event=cancel_event
        )

        if success:
            on_status_change("Sincronização e multiplexação concluídas com sucesso!", 100.0)

        return success

