"""Temporal transform and time-stretch filter without pitch modification using ffmpeg."""

import logging
import os
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


DEFAULT_FFMPEG_THREADS = 2


def _build_atempo_filter(stretch_ratio: float) -> str:
    """
    Builds an FFmpeg atempo filter chain for any stretch ratio.
    The atempo filter accepts values between 0.5 and 2.0. If outside,
    factors are chained (e.g. 2.5 -> atempo=2.0,atempo=1.25).
    """
    factors = []
    curr = stretch_ratio

    while curr > 2.0:
        factors.append("atempo=2.0")
        curr /= 2.0
    while curr < 0.5:
        factors.append("atempo=0.5")
        curr /= 0.5

    factors.append(f"atempo={curr:.6f}")
    return ",".join(factors)


def build_pitch_restoration_filter(
    input_fps: float = 25.0,
    output_fps: float = 24.0,
    target_sr: int = 48000
) -> str:
    """
    Builds an FFmpeg filter chain that decelerates PAL 25fps audio to film 24fps (or 23.976fps)
    with natural analog pitch drop restoration using asetrate + aresample (soxr engine).
    Filter: asetrate=r=<target_sr>*<output_fps>/<input_fps>,aresample=resampler=soxr:osr=<target_sr>
    """
    ratio = output_fps / input_fps
    sample_rate_rescaled = int(round(target_sr * ratio))
    return f"asetrate=r={sample_rate_rescaled},aresample=resampler=soxr:osr={target_sr}"


def apply_temporal_transform(
    audio_in: str,
    audio_out: str,
    offset_ms: float = 0.0,
    stretch_ratio: float = 1.0,
    source_track_id: Optional[int] = None,
    pal_pitch_restore: bool = False,
    audio_codec: str = "flac",
    channels: int = 2
) -> str:
    """
    Applies pitch-neutral time-stretching or PAL pitch restoration to an audio file using FFmpeg.
    
    Args:
        audio_in: Path to input audio or MKV file.
        audio_out: Path to output audio file.
        offset_ms: Optional offset in ms to pre-pad or trim if requested.
        stretch_ratio: Factor to speed up (> 1.0) or slow down (< 1.0).
        source_track_id: Specific container track ID if audio_in is a container.
        pal_pitch_restore: When True, uses asetrate+aresample for natural PAL (25fps -> 24fps) pitch drop.
        audio_codec: Codec to re-encode to: 'flac', 'opus', 'eac3', or 'aac'.
        channels: Channel count to configure appropriate bitrates.
        
    Returns:
        Absolute path to the transformed audio file.
    """
    if not os.path.isfile(audio_in):
        raise FileNotFoundError(f"Input audio not found: {audio_in}")

    os.makedirs(os.path.dirname(os.path.abspath(audio_out)), exist_ok=True)

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-threads", str(DEFAULT_FFMPEG_THREADS),
        "-i", audio_in
    ]

    if source_track_id is not None:
        cmd.extend(["-map", f"0:{source_track_id}"])
    else:
        cmd.extend(["-map", "0:a:0"])

    filters = []

    # Choose filter: PAL pitch restoration or standard atempo pitch-neutral stretch
    if pal_pitch_restore:
        # PAL slowdown 25 -> 24 (or exact stretch_ratio)
        if abs(stretch_ratio - 1.0) >= 0.0001:
            out_fps = 25.0 * stretch_ratio
            filters.append(build_pitch_restoration_filter(input_fps=25.0, output_fps=out_fps, target_sr=48000))
        else:
            filters.append(build_pitch_restoration_filter(input_fps=25.0, output_fps=24.0, target_sr=48000))
    elif abs(stretch_ratio - 1.0) >= 0.0001:
        filters.append(_build_atempo_filter(stretch_ratio))

    if filters:
        cmd.extend(["-filter:a", ",".join(filters)])

    # Output codec configuration
    codec_lower = audio_codec.lower()
    if codec_lower == "opus":
        # 160k for stereo 2.0, 450k for 5.1/7.1 surround
        bitrate = "450k" if channels >= 6 else "160k"
        cmd.extend(["-c:a", "libopus", "-b:a", bitrate])
    elif codec_lower in ("eac3", "ac3"):
        bitrate = "640k" if channels >= 6 else "384k"
        cmd.extend(["-c:a", codec_lower, "-b:a", bitrate])
    elif codec_lower == "aac":
        bitrate = "384k" if channels >= 6 else "256k"
        cmd.extend(["-c:a", "aac", "-b:a", bitrate])
    else:
        # Default lossless FLAC
        cmd.extend(["-c:a", "flac"])

    cmd.append(audio_out)

    logger.info("Executing temporal transform: %s", " ".join(cmd))
    res = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if res.returncode != 0:
        raise RuntimeError(f"Audio temporal transform failed (code {res.returncode}): {res.stderr.strip()}")

    if not os.path.exists(audio_out) or os.path.getsize(audio_out) == 0:
        raise RuntimeError(f"Output transformed audio missing or empty: {audio_out}")

    return audio_out
