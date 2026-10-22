"""Disk space pre-flight validation utility."""

import logging
import os
import shutil
from typing import Tuple

logger = logging.getLogger(__name__)


def format_bytes(size_bytes: int) -> str:
    """Formats bytes into human-readable string (KB, MB, GB, TB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    for unit in ["KB", "MB", "GB", "TB"]:
        size_bytes /= 1024.0
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
    return f"{size_bytes:.2f} PB"


def check_disk_space(
    destination_path: str,
    video_source_path: str,
    audio_source_path: str,
    safety_margin_ratio: float = 0.15
) -> Tuple[bool, int, int]:
    """
    Checks if there is sufficient free disk space to store the remuxed MKV file.
    
    Args:
        destination_path: Planned output file path.
        video_source_path: Path to original video file.
        audio_source_path: Path to target audio file.
        safety_margin_ratio: Additional safety margin (default 15%).
        
    Returns:
        (is_sufficient, free_bytes, required_bytes)
    """
    target_dir = os.path.dirname(os.path.abspath(destination_path))
    # If target directory does not exist yet, inspect parent
    while not os.path.exists(target_dir):
        parent = os.path.dirname(target_dir)
        if parent == target_dir:
            break
        target_dir = parent

    total, used, free = shutil.disk_usage(target_dir)

    video_size = os.path.getsize(video_source_path) if os.path.isfile(video_source_path) else 0
    audio_size = os.path.getsize(audio_source_path) if os.path.isfile(audio_source_path) else 0

    estimated_output_size = int((video_size + audio_size) * (1.0 + safety_margin_ratio))

    is_sufficient = free >= estimated_output_size

    if not is_sufficient:
        logger.warning(
            "Insufficient disk space in %s. Free: %s, Required: %s",
            target_dir, format_bytes(free), format_bytes(estimated_output_size)
        )

    return is_sufficient, free, estimated_output_size
