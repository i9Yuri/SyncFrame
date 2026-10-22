"""Lossless MKV remuxing orchestrator using mkvmerge."""

import logging
import os
import re
import subprocess
import threading
from typing import Callable, Optional

from .models import RemuxJob
from .transformer import apply_temporal_transform
from .temp_manager import TempWorkspace

logger = logging.getLogger(__name__)

PROGRESS_REGEX = re.compile(r"Progress:\s*(\d+)%", re.IGNORECASE)


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
    - 0% audio recompression if only a static offset is needed (--sync container flag).
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

        # Check if time-stretch is needed due to framerate drift
        needs_stretch = abs(job.stretch_ratio - 1.0) >= 0.0001
        if needs_stretch:
            if on_progress:
                on_progress(5.0, f"Aplicando time-stretch ({job.stretch_ratio:.6f}) na faixa dublada...")
            
            stretched_wav = staging.get_path("dubbed_stretched.flac")
            apply_temporal_transform(
                audio_in=job.target_audio_file,
                audio_out=stretched_wav,
                offset_ms=0.0,
                stretch_ratio=job.stretch_ratio,
                source_track_id=job.target_track_id
            )
            audio_to_mux = stretched_wav
            target_track_id = 0  # In extracted FLAC, audio is track 0

        if cancel_event and cancel_event.is_set():
            logger.info("Remux cancelled by user before mkvmerge launch.")
            return False

        # Build mkvmerge command
        cmd = ["mkvmerge", "-o", job.output_path]

        # 1. Video source options
        cmd.extend(["--video-tracks", str(job.video_track_id)])

        if job.keep_original_audio:
            cmd.extend([
                "--audio-tracks", str(job.ref_audio_track_id),
                f"--default-track-flag", f"{job.ref_audio_track_id}:no",
                f"--track-name", f"{job.ref_audio_track_id}:{job.original_audio_name}",
                f"--language", f"{job.ref_audio_track_id}:{job.original_audio_language}",
            ])
        else:
            cmd.append("--no-audio")

        cmd.extend(["--no-subtitles", "--no-attachments", job.video_file])

        # 2. Synchronized Dubbed Audio source options
        int_offset_ms = int(round(job.offset_ms))
        cmd.extend([
            "--audio-tracks", str(target_track_id),
            "--sync", f"{target_track_id}:{int_offset_ms}",
            "--default-track-flag", f"{target_track_id}:yes",
            "--track-name", f"{target_track_id}:{job.target_audio_name}",
            "--language", f"{target_track_id}:{job.target_audio_language}",
            "--no-video", "--no-subtitles", "--no-attachments",
            audio_to_mux
        ])

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
                        # Scale progress from 10% to 100%
                        scaled_pct = 10.0 + (pct * 0.9)
                        on_progress(scaled_pct, clean_line)
                    elif on_progress:
                        on_progress(-1.0, clean_line)

            retcode = proc.wait()
            if retcode not in (0, 1):  # 0 = success, 1 = warnings (normal in mkvmerge)
                raise RuntimeError(f"mkvmerge remux failed with exit code {retcode}")

            if on_progress:
                on_progress(100.0, "Multiplexação concluída com sucesso!")

            return True

        except Exception as exc:
            proc.terminate()
            if os.path.exists(job.output_path):
                try:
                    os.remove(job.output_path)
                except OSError:
                    pass
            raise exc
