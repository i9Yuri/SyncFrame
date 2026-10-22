"""Audio extraction and acoustic preprocessing pipeline using ffmpeg."""

import logging
import os
import subprocess
from typing import Optional

from .temp_manager import TempWorkspace

logger = logging.getLogger(__name__)


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
    
    Returns:
        Absolute path to the resulting WAV file.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Input media file not found: {file_path}")

    if not output_path:
        # Default into a new temporary workspace file
        workspace = TempWorkspace()
        output_path = workspace.get_path(f"track_{stream_id}_{int(start_sec)}_{target_sr}hz.wav")
    else:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Build ffmpeg command
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]

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
        # 300Hz highpass to remove hums/DC; 4000Hz lowpass to attenuate high-frequency vocal sibilance
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
