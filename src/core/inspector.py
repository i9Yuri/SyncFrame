"""Media stream inspector using mkvmerge -J and ffprobe."""

import json
import logging
import os
import subprocess
from typing import List, Optional, Tuple, Dict, Any

from .models import StreamMetadata, InspectionResult

logger = logging.getLogger(__name__)


def _parse_fraction(frac_str: str) -> float:
    """Safely parse rational fraction strings like '24000/1001' or '25/1' into float."""
    if not frac_str or frac_str == "0/0":
        return 0.0
    try:
        if "/" in frac_str:
            num, den = frac_str.split("/", 1)
            num_f, den_f = float(num), float(den)
            return (num_f / den_f) if den_f != 0.0 else 0.0
        return float(frac_str)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0


def _inspect_via_mkvmerge(file_path: str) -> List[StreamMetadata]:
    """Inspect MKV or media file using mkvmerge -J to get exact container track IDs."""
    streams: List[StreamMetadata] = []
    try:
        cmd = ["mkvmerge", "-J", file_path]
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        data = json.loads(res.stdout)
        tracks = data.get("tracks", [])
        container_duration_ms = 0.0
        container_props = data.get("container", {}).get("properties", {})
        if "duration" in container_props:
            # mkvmerge reports duration in nanoseconds
            container_duration_ms = float(container_props["duration"]) / 1_000_000.0

        for t in tracks:
            track_id = int(t.get("id", 0))
            track_type = str(t.get("type", "")).lower()
            codec = str(t.get("codec", ""))
            props = t.get("properties", {})
            
            channels = int(props.get("audio_channels", 0))
            sample_rate = int(props.get("audio_sampling_frequency", 0))
            language = str(props.get("language", props.get("language_ietf", "und")))
            is_default = bool(props.get("default_track", False))
            title = str(props.get("track_name", ""))
            codec_id = str(props.get("codec_id", ""))
            
            width = props.get("pixel_dimensions", "").split("x")[0] if "pixel_dimensions" in props else None
            height = props.get("pixel_dimensions", "").split("x")[1] if "pixel_dimensions" in props and "x" in props.get("pixel_dimensions", "") else None
            
            width_int = int(width) if width and str(width).isdigit() else None
            height_int = int(height) if height and str(height).isdigit() else None
            
            fps = 0.0
            if "default_duration" in props:
                # default_duration is in nanoseconds per frame
                nanosecs = float(props["default_duration"])
                if nanosecs > 0:
                    fps = 1_000_000_000.0 / nanosecs

            duration_ms = container_duration_ms

            streams.append(StreamMetadata(
                id=track_id,
                codec=codec,
                channels=channels,
                sample_rate=sample_rate,
                fps=fps,
                duration_ms=duration_ms,
                language=language,
                is_default=is_default,
                track_type=track_type,
                title=title,
                codec_id=codec_id,
                width=width_int,
                height=height_int
            ))
    except Exception as exc:
        logger.warning("mkvmerge -J inspection failed for %s: %s", file_path, exc)
    return streams


def _inspect_via_ffprobe(file_path: str) -> List[StreamMetadata]:
    """Inspect media file using ffprobe as primary or fallback parser."""
    streams: List[StreamMetadata] = []
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        data = json.loads(res.stdout)
        format_info = data.get("format", {})
        container_duration_sec = float(format_info.get("duration", 0.0))
        container_duration_ms = container_duration_sec * 1000.0

        for s in data.get("streams", []):
            codec_type = s.get("codec_type", "").lower()
            if codec_type not in ("video", "audio"):
                continue

            stream_index = int(s.get("index", 0))
            codec = s.get("codec_name", "")
            channels = int(s.get("channels", 0))
            sample_rate = int(s.get("sample_rate", 0))
            
            fps = _parse_fraction(s.get("r_frame_rate", ""))
            if fps == 0.0:
                fps = _parse_fraction(s.get("avg_frame_rate", ""))

            tags = s.get("tags", {})
            language = tags.get("language", "und")
            title = tags.get("title", "")
            
            disposition = s.get("disposition", {})
            is_default = bool(disposition.get("default", 0))

            duration_sec = float(s.get("duration", container_duration_sec))
            duration_ms = duration_sec * 1000.0 if duration_sec > 0 else container_duration_ms

            width = s.get("width")
            height = s.get("height")

            streams.append(StreamMetadata(
                id=stream_index,
                codec=codec,
                channels=channels,
                sample_rate=sample_rate,
                fps=fps,
                duration_ms=duration_ms,
                language=language,
                is_default=is_default,
                track_type=codec_type,
                title=title,
                width=width,
                height=height
            ))
    except Exception as exc:
        logger.error("ffprobe inspection failed for %s: %s", file_path, exc)
    return streams


def inspect_media(file_path: str) -> List[StreamMetadata]:
    """
    Inspects media file and returns list of StreamMetadata.
    Prefers mkvmerge -J to preserve container track IDs, enriching with ffprobe if needed.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Media file not found: {file_path}")

    # Primary inspection via mkvmerge for MKV container fidelity
    mkv_streams = _inspect_via_mkvmerge(file_path)
    if mkv_streams:
        # Check if FPS or resolution needs enrichment via ffprobe
        needs_enrichment = any(s.track_type == "video" and (s.fps == 0.0 or not s.width) for s in mkv_streams)
        if needs_enrichment:
            ff_streams = _inspect_via_ffprobe(file_path)
            ff_dict = {s.id: s for s in ff_streams}
            for s in mkv_streams:
                if s.id in ff_dict:
                    ff = ff_dict[s.id]
                    if s.fps == 0.0:
                        s.fps = ff.fps
                    if not s.width:
                        s.width = ff.width
                        s.height = ff.height
        return mkv_streams

    # Fallback directly to ffprobe
    return _inspect_via_ffprobe(file_path)


def get_inspection_result(video_source: str, audio_source: str) -> InspectionResult:
    """
    Inspects both video source and target audio source containers and selects defaults.
    """
    video_streams = inspect_media(video_source)
    audio_streams = inspect_media(audio_source)

    all_video = [s for s in video_streams if s.track_type == "video"]
    all_audio_in_video = [s for s in video_streams if s.track_type == "audio"]
    all_audio_in_audio = [s for s in audio_streams if s.track_type == "audio"]

    # Select primary video track
    selected_video = all_video[0] if all_video else None

    # Select reference audio track (prefer original/english or default in video container)
    ref_audio = None
    if all_audio_in_video:
        # Prefer default track or english
        english_tracks = [s for s in all_audio_in_video if s.language.lower() in ("eng", "en")]
        default_tracks = [s for s in all_audio_in_video if s.is_default]
        if english_tracks:
            ref_audio = english_tracks[0]
        elif default_tracks:
            ref_audio = default_tracks[0]
        else:
            ref_audio = all_audio_in_video[0]

    # Select target audio track (prefer portuguese in audio container)
    target_audio = None
    if all_audio_in_audio:
        pt_tracks = [s for s in all_audio_in_audio if s.language.lower() in ("por", "pt", "pob", "pt-br", "bra")]
        default_tracks = [s for s in all_audio_in_audio if s.is_default]
        if pt_tracks:
            target_audio = pt_tracks[0]
        elif default_tracks:
            target_audio = default_tracks[0]
        else:
            target_audio = all_audio_in_audio[0]

    return InspectionResult(
        video_source=video_source,
        audio_source=audio_source,
        selected_video_stream=selected_video,
        ref_audio_stream=ref_audio,
        target_audio_stream=target_audio,
        all_video_streams=all_video,
        all_audio_streams_video=all_audio_in_video,
        all_audio_streams_audio=all_audio_in_audio
    )
