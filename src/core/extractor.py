"""Audio extraction and acoustic preprocessing pipeline using ffmpeg."""

import logging
import os
import subprocess
from typing import Optional

from .models import ExtractedAudioResult
from .temp_manager import TempWorkspace

logger = logging.getLogger(__name__)


DEFAULT_FFMPEG_THREADS = 2


def extract_reference_channel(
    file_path: str,
    stream_id: int,
    target_sr: int = 16000,
    duration_sec: Optional[float] = None,
    start_sec: float = 0.0,
    output_path: Optional[str] = None,
    apply_bandpass: bool = True
) -> str:
    """
    Extracts a simplified mono PCM 16kHz WAV channel from a specific container audio track.
    Applies a bandpass filter (300Hz-4000Hz) to suppress language-dependent speech fundamentals
    and isolate background foley, transients, and soundtrack cues for high mutual coherence.
    Limits FFmpeg execution to a safe thread count (-threads 2) to avoid thermal and power spikes.
    
    Returns:
        Absolute path to the resulting WAV file.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Input media file not found: {file_path}")

    if not output_path:
        workspace = TempWorkspace()
        output_path = workspace.get_path(f"track_{stream_id}_{int(start_sec)}_{target_sr}hz.wav")
    else:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Build ffmpeg command with error resilience and thread throttling
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-threads", str(DEFAULT_FFMPEG_THREADS),
        "-err_detect", "ignore_err"
    ]

    # Fast seek if start_sec > 0
    if start_sec > 0.0:
        cmd.extend(["-ss", f"{start_sec:.3f}"])

    cmd.extend(["-i", file_path])

    if duration_sec is not None and duration_sec > 0.0:
        cmd.extend(["-t", f"{duration_sec:.3f}"])

    cmd.extend([
        "-map", f"0:{stream_id}",
        "-vn", "-sn", "-dn",
        "-ac", "1",
        "-ar", str(target_sr),
    ])

    if apply_bandpass:
        cmd.extend(["-af", "highpass=f=300,lowpass=f=4000"])

    cmd.extend([
        "-c:a", "pcm_s16le",
        output_path
    ])

    logger.debug("Executing audio extraction: %s", " ".join(cmd))
    res = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed (code {res.returncode}): {res.stderr.strip()}")

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise RuntimeError(f"FFmpeg completed but output file is missing or empty: {output_path}")

    return output_path


def extract_audio_lossless(
    input_path: str,
    track_index: int,
    output_dir: str
) -> ExtractedAudioResult:
    """
    Extracts an audio stream from an input media container using stream copy (-c:a copy).
    Guarantees 0% recompression for standard codecs (AAC, AC3, EAC3, MP3, Opus, DTS, FLAC).
    If direct stream copy fails (e.g. bitstream filter required or container restriction),
    falls back cleanly to lossless multichannel FLAC (-c:a flac) without loss of fidelity.
    """
    from .inspector import probe_media_file

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input media file not found: {input_path}")

    os.makedirs(output_dir, exist_ok=True)
    probe_info = probe_media_file(input_path)

    # Locate target audio stream
    target_stream = None
    for s in probe_info.audio_streams:
        if s.id == track_index:
            target_stream = s
            break
    if not target_stream and probe_info.audio_streams:
        target_stream = probe_info.audio_streams[0]

    raw_codec = target_stream.codec.lower() if target_stream else "flac"
    channels = target_stream.channels if target_stream else 2
    sample_rate = target_stream.sample_rate if target_stream else 48000

    # Determine standard container extension for direct copy
    if raw_codec == "aac":
        ext = ".m4a"
    elif raw_codec in ("ac3", "eac3", "flac", "mp3", "opus", "dts"):
        ext = f".{raw_codec}"
    elif raw_codec == "dca":
        ext = ".dts"
    elif "pcm" in raw_codec:
        ext = ".wav"
    else:
        ext = ".flac"

    output_path = os.path.join(output_dir, f"track_{track_index}_copy{ext}")
    is_direct_copy = False

    if ext != ".flac" or raw_codec == "flac":
        cmd_copy = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-threads", str(DEFAULT_FFMPEG_THREADS),
            "-err_detect", "ignore_err",
            "-i", input_path,
            "-map", f"0:{track_index}",
            "-vn", "-sn", "-dn",
            "-c:a", "copy",
            output_path
        ]
        res = subprocess.run(cmd_copy, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            is_direct_copy = True

    if not is_direct_copy:
        # Fallback: lossless multichannel FLAC
        output_flac = os.path.join(output_dir, f"track_{track_index}_lossless.flac")
        cmd_flac = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-threads", str(DEFAULT_FFMPEG_THREADS),
            "-err_detect", "ignore_err",
            "-i", input_path,
            "-map", f"0:{track_index}",
            "-vn", "-sn", "-dn",
            "-c:a", "flac",
            output_flac
        ]
        res_flac = subprocess.run(cmd_flac, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res_flac.returncode != 0 or not os.path.exists(output_flac) or os.path.getsize(output_flac) == 0:
            raise RuntimeError(f"Lossless audio demuxing failed: {res_flac.stderr.strip()}")
        output_path = output_flac
        raw_codec = "flac"

    return ExtractedAudioResult(
        output_path=output_path,
        codec=raw_codec,
        is_direct_copy=is_direct_copy,
        channels=channels,
        sample_rate=sample_rate
    )
