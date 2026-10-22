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


def apply_temporal_transform(
    audio_in: str,
    audio_out: str,
    offset_ms: float = 0.0,
    stretch_ratio: float = 1.0,
    source_track_id: Optional[int] = None
) -> str:
    """
    Applies pitch-neutral time-stretching to an audio file using FFmpeg's atempo filter.
    Preserves maximum audio fidelity by outputting to lossless FLAC or PCM.
    
    Args:
        audio_in: Path to input audio or MKV file.
        audio_out: Path to output audio file.
        offset_ms: Optional offset in ms to pre-pad or trim if requested.
        stretch_ratio: Factor to speed up (> 1.0) or slow down (< 1.0).
        source_track_id: Specific container track ID if audio_in is a container.
        
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

    # Time stretch filter
    if abs(stretch_ratio - 1.0) >= 0.0001:
        filters.append(_build_atempo_filter(stretch_ratio))

    if filters:
        cmd.extend(["-filter:a", ",".join(filters)])

    # Output in lossless FLAC to prevent transcoding quality degradation
    cmd.extend(["-c:a", "flac", audio_out])

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
