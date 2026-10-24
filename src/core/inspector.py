"""Media stream inspector using mkvmerge -J and deep ffprobe probing."""

import json
import logging
import os
import subprocess
from typing import List, Optional, Tuple, Dict, Any

from .models import (
    StreamMetadata,
    InspectionResult,
    StreamCandidate,
    AutoMatchVerdict,
    AudioProfile,
    MediaContainerInfo,
    ContainerTimeOffsets,
    format_channel_layout_label,
    AudioQualityScore,
    StreamArbitrationResult
)

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


def probe_media_file(file_path: str) -> MediaContainerInfo:
    """
    Performs deep inspection of any media container (MKV, MP4, M4V, MOV) using ffprobe
    with robust parameters (-analyzeduration 100M -probesize 50M) and fallback for
    malformed/corrupted headers (-err_detect ignore_err).
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Media file not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    container_format = ext if ext in ("mkv", "mp4", "m4v", "mov") else "unknown"

    base_cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        "-analyzeduration", "100M",
        "-probesize", "50M",
    ]

    is_corrupted = False
    data = None
    try:
        cmd = base_cmd + [file_path]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(res.stdout)
    except Exception as exc:
        logger.warning(
            "Standard ffprobe probing failed for %s (%s). Attempting error-resilient fallback...",
            file_path, exc
        )
        try:
            cmd = base_cmd + ["-err_detect", "ignore_err", file_path]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            data = json.loads(res.stdout)
            is_corrupted = True
        except Exception as exc2:
            logger.error("Deep ffprobe inspection completely failed for %s: %s", file_path, exc2)
            raise RuntimeError(f"Unable to probe media file {file_path}: {exc2}") from exc2

    format_info = data.get("format", {})
    if container_format == "unknown":
        fmt_name = format_info.get("format_name", "").lower()
        if "matroska" in fmt_name:
            container_format = "mkv"
        elif "mp4" in fmt_name or "mov" in fmt_name or "m4a" in fmt_name:
            container_format = "mp4"

    container_duration_sec = float(format_info.get("duration", 0.0))
    container_duration_ms = container_duration_sec * 1000.0

    video_streams: List[StreamMetadata] = []
    audio_streams: List[StreamMetadata] = []
    all_streams: List[StreamMetadata] = []

    for s in data.get("streams", []):
        codec_type = s.get("codec_type", "").lower()
        if codec_type not in ("video", "audio"):
            continue

        stream_index = int(s.get("index", 0))
        codec = s.get("codec_name", "")
        channels = int(s.get("channels", 0))
        channel_layout = str(s.get("channel_layout", ""))
        sample_rate = int(s.get("sample_rate", 0))

        bitrate_str = s.get("bit_rate") or format_info.get("bit_rate")
        bitrate_int = int(bitrate_str) if bitrate_str and str(bitrate_str).isdigit() else None

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
        width_int = int(width) if width and str(width).isdigit() else None
        height_int = int(height) if height and str(height).isdigit() else None

        # Parse side data and start time offsets
        stream_start_time_sec = float(s.get("start_time", 0.0) or 0.0)
        stream_start_time_ms = stream_start_time_sec * 1000.0

        # Check for edit list (elst) in side_data_list or tags
        edit_list_offset_ms = 0.0
        for side_data in s.get("side_data_list", []):
            side_type = str(side_data.get("side_data_type", "")).lower()
            if "edit list" in side_type or "elst" in side_type:
                # If initial media time or start time is specified
                media_time = side_data.get("media_time")
                if media_time is not None:
                    edit_list_offset_ms = float(media_time) / 1000.0

        container_start_sec = float(format_info.get("start_time", 0.0) or 0.0)
        container_start_ms = container_start_sec * 1000.0

        stream_time_offsets = ContainerTimeOffsets(
            format_start_time_ms=container_start_ms,
            stream_start_time_ms=stream_start_time_ms,
            edit_list_offset_ms=edit_list_offset_ms,
            net_adjustment_ms=stream_start_time_ms + edit_list_offset_ms
        )

        audio_profile = None
        if codec_type == "audio":
            audio_profile = AudioProfile(
                codec=codec,
                channels=channels,
                channel_layout=channel_layout,
                sample_rate=sample_rate,
                bit_rate=bitrate_int,
                is_surround=(channels >= 6 or "5.1" in channel_layout or "7.1" in channel_layout)
            )

        meta = StreamMetadata(
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
            bitrate=bitrate_int,
            width=width_int,
            height=height_int,
            channel_layout=channel_layout,
            container_format=container_format,
            audio_profile=audio_profile,
            container_time_offsets=stream_time_offsets
        )

        all_streams.append(meta)
        if codec_type == "video":
            video_streams.append(meta)
        elif codec_type == "audio":
            audio_streams.append(meta)

    container_start_sec = float(format_info.get("start_time", 0.0) or 0.0)
    container_offsets = ContainerTimeOffsets(
        format_start_time_ms=container_start_sec * 1000.0,
        stream_start_time_ms=audio_streams[0].container_time_offsets.stream_start_time_ms if (audio_streams and audio_streams[0].container_time_offsets) else 0.0,
        edit_list_offset_ms=audio_streams[0].container_time_offsets.edit_list_offset_ms if (audio_streams and audio_streams[0].container_time_offsets) else 0.0,
        net_adjustment_ms=container_start_sec * 1000.0
    )

    return MediaContainerInfo(
        file_path=file_path,
        container_format=container_format,
        duration_ms=container_duration_ms,
        video_streams=video_streams,
        audio_streams=audio_streams,
        all_streams=all_streams,
        is_corrupted=is_corrupted,
        container_time_offsets=container_offsets
    )


def extract_container_time_offsets(file_path: str, stream_index: Optional[int] = None) -> ContainerTimeOffsets:
    """
    Extracts deterministic start_time and edit list (elst) timestamps from any media container
    using ffprobe with side_data extraction.
    """
    if not os.path.isfile(file_path):
        return ContainerTimeOffsets()

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        "-show_entries", "format=start_time:stream=index,codec_type,start_time:stream_side_data_list",
        file_path
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(res.stdout)
    except Exception as exc:
        logger.warning("Failed to probe container timestamps for %s: %s", file_path, exc)
        return ContainerTimeOffsets()

    format_info = data.get("format", {})
    fmt_start_sec = float(format_info.get("start_time", 0.0) or 0.0)
    fmt_start_ms = fmt_start_sec * 1000.0

    target_stream = None
    streams = data.get("streams", [])
    if stream_index is not None:
        for s in streams:
            if s.get("index") == stream_index:
                target_stream = s
                break

    if target_stream is None:
        # Default to first audio stream, or first stream
        audio_s = [s for s in streams if s.get("codec_type") == "audio"]
        target_stream = audio_s[0] if audio_s else (streams[0] if streams else {})

    stream_start_sec = float(target_stream.get("start_time", 0.0) or 0.0)
    stream_start_ms = stream_start_sec * 1000.0

    edit_list_ms = 0.0
    for side in target_stream.get("side_data_list", []):
        st = str(side.get("side_data_type", "")).lower()
        if "edit list" in st or "elst" in st:
            m_time = side.get("media_time")
            if m_time is not None:
                edit_list_ms = float(m_time) / 1000.0

    net_adj = (stream_start_ms if stream_start_ms != 0.0 else fmt_start_ms) + edit_list_ms

    return ContainerTimeOffsets(
        format_start_time_ms=fmt_start_ms,
        stream_start_time_ms=stream_start_ms,
        edit_list_offset_ms=edit_list_ms,
        net_adjustment_ms=net_adj
    )


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
                nanosecs = float(props["default_duration"])
                if nanosecs > 0:
                    fps = 1_000_000_000.0 / nanosecs

            duration_ms = container_duration_ms

            audio_profile = None
            if track_type == "audio":
                audio_profile = AudioProfile(
                    codec=codec,
                    channels=channels,
                    channel_layout=f"{channels}.0" if channels in (1, 2) else ("5.1" if channels == 6 else f"{channels}ch"),
                    sample_rate=sample_rate,
                    is_surround=(channels >= 6)
                )

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
                height=height_int,
                container_format="mkv",
                audio_profile=audio_profile
            ))
    except Exception as exc:
        logger.warning("mkvmerge -J inspection failed for %s: %s", file_path, exc)
    return streams


def inspect_media(file_path: str) -> List[StreamMetadata]:
    """
    Inspects media file and returns list of StreamMetadata.
    For MKV files, uses mkvmerge -J to retain native track IDs, enriched by ffprobe deep probe.
    For MP4, M4V, MOV and other containers, uses probe_media_file directly.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Media file not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".mkv":
        mkv_streams = _inspect_via_mkvmerge(file_path)
        if mkv_streams:
            try:
                probe_info = probe_media_file(file_path)
                ff_dict = {s.id: s for s in probe_info.all_streams}
                ff_audios = probe_info.audio_streams
                audio_idx = 0
                for s in mkv_streams:
                    s.container_format = "mkv"
                    if s.id in ff_dict:
                        ff = ff_dict[s.id]
                        if s.fps == 0.0:
                            s.fps = ff.fps
                        if not s.width:
                            s.width = ff.width
                            s.height = ff.height
                        if s.track_type == "audio":
                            s.channel_layout = ff.channel_layout
                            s.audio_profile = ff.audio_profile
                            s.bitrate = s.bitrate or ff.bitrate
                    elif s.track_type == "audio" and audio_idx < len(ff_audios):
                        ff = ff_audios[audio_idx]
                        s.channel_layout = ff.channel_layout
                        s.audio_profile = ff.audio_profile
                        s.bitrate = s.bitrate or ff.bitrate
                        audio_idx += 1
            except Exception as exc:
                logger.debug("Enrichment via ffprobe skipped for %s: %s", file_path, exc)
            return mkv_streams

    probe_info = probe_media_file(file_path)
    return probe_info.all_streams


def get_inspection_result(video_source: str, audio_source: str) -> InspectionResult:
    """
    Inspects both video source and target audio source containers and selects defaults.
    """
    video_streams = inspect_media(video_source)
    audio_streams = inspect_media(audio_source)

    all_video = [s for s in video_streams if s.track_type == "video"]
    all_audio_in_video = [s for s in video_streams if s.track_type == "audio"]
    all_audio_in_audio = [s for s in audio_streams if s.track_type == "audio"]

    selected_video = all_video[0] if all_video else None

    ref_audio = None
    if all_audio_in_video:
        english_tracks = [s for s in all_audio_in_video if s.language.lower() in ("eng", "en")]
        default_tracks = [s for s in all_audio_in_video if s.is_default]
        if english_tracks:
            ref_audio = english_tracks[0]
        elif default_tracks:
            ref_audio = default_tracks[0]
        else:
            ref_audio = all_audio_in_video[0]

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


# Codec efficiency weights
CODEC_EFFICIENCY_WEIGHTS = {
    "av1": 1.4,
    "hevc": 1.2,
    "h265": 1.2,
    "h.265": 1.2,
    "vp9": 1.15,
    "avc": 1.0,
    "h264": 1.0,
    "h.264": 1.0,
    "vc1": 0.8,
    "mpeg4": 0.8,
    "mpeg2": 0.7,
}

PORTUGUESE_TAGS = {"por", "pt", "pt-br", "pob", "bra", "ptb"}
PORTUGUESE_KEYWORDS = ("dublado", "portuguese", "português", "nacional", "brazilian", "dub")
ENGLISH_TAGS = {"eng", "en", "original"}


def _get_codec_weight(codec_name: str) -> float:
    normalized = codec_name.lower().replace(" ", "").replace("-", "")
    for k, w in CODEC_EFFICIENCY_WEIGHTS.items():
        if k in normalized:
            return w
    return 1.0


def rank_video_streams(streams_with_files: List[Tuple[str, StreamMetadata]]) -> List[StreamCandidate]:
    """
    Ranks video streams across all provided files using deterministic fidelity scoring:
    Score = (Resolution Area * Codec Weight) + (Bitrate in kbps * 50.0).
    Returns sorted list of StreamCandidate (highest score first).
    """
    candidates: List[StreamCandidate] = []

    for file_path, stream in streams_with_files:
        if stream.track_type != "video":
            continue

        w = stream.width or 0
        h = stream.height or 0
        pixels = w * h
        codec_wt = _get_codec_weight(stream.codec)

        bitrate_bps = stream.bitrate or 0
        if bitrate_bps == 0 and os.path.isfile(file_path):
            file_bytes = os.path.getsize(file_path)
            dur_sec = (stream.duration_ms / 1000.0) if stream.duration_ms > 0 else 7200.0
            bitrate_bps = int((file_bytes * 8.0) / dur_sec)

        bitrate_kbps = bitrate_bps / 1000.0
        score = (pixels * 1.0 * codec_wt) + (bitrate_kbps * 50.0)

        res_label = f"{w}x{h}" if w and h else "Resolução Indefinida"
        fmt_label = stream.container_format.upper() if stream.container_format else "MKV"
        details = f"{res_label} ({stream.codec.upper()}) [{fmt_label}] | ~{bitrate_kbps:.0f} kbps"

        candidates.append(StreamCandidate(
            stream=stream,
            file_path=file_path,
            score=score,
            is_recommended=False,
            badge_label="",
            details_str=details
        ))

    candidates.sort(key=lambda c: c.score, reverse=True)

    if candidates:
        candidates[0].is_recommended = True
        candidates[0].badge_label = "Melhor Qualidade Detectada"

    return candidates


def identify_target_and_ref_audios(
    streams_with_files: List[Tuple[str, StreamMetadata]],
    chosen_video_file: str
) -> Tuple[Optional[StreamCandidate], Optional[StreamCandidate], List[StreamCandidate], bool, str]:
    """
    Scans all audio streams across both containers to elect:
    1. Target dubbed audio stream (Portuguese tags or keywords, preferred from opposite container).
    2. Reference audio stream (Original/English from the chosen video container).
    
    Returns:
        (recommended_target, reference_audio, all_target_candidates, is_ambiguous, ambiguity_reason)
    """
    audio_candidates: List[Tuple[float, StreamCandidate, bool]] = []
    has_explicit_pt = False

    for file_path, stream in streams_with_files:
        if stream.track_type != "audio":
            continue

        lang_lower = stream.language.lower() if stream.language else ""
        title_lower = stream.title.lower() if stream.title else ""

        is_pt_lang = lang_lower in PORTUGUESE_TAGS
        is_pt_title = any(kw in title_lower for kw in PORTUGUESE_KEYWORDS)
        is_pt = is_pt_lang or is_pt_title

        if is_pt:
            has_explicit_pt = True

        score = 0.0
        if is_pt_lang:
            score += 1000.0
        if is_pt_title:
            score += 800.0
        if file_path != chosen_video_file:
            # Strong bonus if coming from the separate dubbed release file
            score += 350.0
            # If opposite file has only 1 audio stream, strong probability it's the target dub
            opp_audios = [s for f, s in streams_with_files if f == file_path and s.track_type == "audio"]
            if len(opp_audios) == 1:
                score += 150.0
        if stream.is_default:
            score += 50.0

        score += (stream.channels or 2) * 20.0
        score += (stream.sample_rate or 48000) / 1000.0

        layout_label = format_channel_layout_label(stream.channels, stream.channel_layout)
        fmt_label = stream.container_format.upper() if stream.container_format else "MKV"
        lang_str = stream.language.upper() if stream.language else "UND"
        sr_label = f"{stream.sample_rate:,}Hz".replace(",", ".") if stream.sample_rate else ""
        details = f"{lang_str} ({stream.codec.upper()} | {layout_label} | {sr_label}) [{fmt_label}]"

        cand = StreamCandidate(
            stream=stream,
            file_path=file_path,
            score=score,
            is_recommended=False,
            badge_label="",
            details_str=details
        )
        audio_candidates.append((score, cand, is_pt))

    audio_candidates.sort(key=lambda x: x[0], reverse=True)
    all_candidates = [x[1] for x in audio_candidates]

    recommended_target = None
    is_ambiguous = False
    ambiguity_reason = ""

    if has_explicit_pt and all_candidates:
        recommended_target = all_candidates[0]
        recommended_target.is_recommended = True
        recommended_target.badge_label = "Áudio Português Identificado"
    elif all_candidates:
        non_video_audios = [c for c in all_candidates if c.file_path != chosen_video_file]
        recommended_target = non_video_audios[0] if non_video_audios else all_candidates[0]
        recommended_target.is_recommended = False
        recommended_target.badge_label = "Atenção: Seleção Manual Sugerida"
        is_ambiguous = True
        ambiguity_reason = "Nenhuma tag ou título em português encontrada nos metadados. Confirme a faixa manualmente."

    video_audios = [c for c in all_candidates if c.file_path == chosen_video_file]
    reference_audio = None

    if video_audios:
        def ref_score(c: StreamCandidate) -> float:
            s = c.stream
            sc = 0.0
            if s.language.lower() in ENGLISH_TAGS:
                sc += 500.0
            if s.is_default:
                sc += 100.0
            sc += (s.channels or 2) * 50.0
            sc += (s.sample_rate or 48000) / 1000.0
            return sc

        video_audios.sort(key=ref_score, reverse=True)
        reference_audio = video_audios[0]
        reference_audio.badge_label = "Áudio Original de Referência"
    elif all_candidates:
        reference_audio = all_candidates[0]

    return recommended_target, reference_audio, all_candidates, is_ambiguous, ambiguity_reason


def get_codec_tier(codec_name: str) -> int:
    """
    Ranks codec preservation tier:
    Tier 5: Lossless/Master (FLAC, TrueHD, DTS-HD MA, PCM, ALAC, WAV)
    Tier 4: High-fidelity lossy (E-AC3/EAC3, DTS, AC3, Opus)
    Tier 3: Standard lossy (AAC)
    Tier 2: Legacy lossy (MP3, MP2, Vorbis, WMA)
    Tier 1: Low-profile/Voice/Unknown
    """
    c = (codec_name or "").lower().replace("-", "").replace("_", "").replace(" ", "")
    if any(k in c for k in ("flac", "truehd", "dtshd", "dtsma", "pcm", "alac", "wav")):
        return 5
    elif any(k in c for k in ("eac3", "dts", "ac3", "opus", "dolby")):
        return 4
    elif "aac" in c:
        return 3
    elif any(k in c for k in ("mp3", "mp2", "vorbis", "ogg", "wma")):
        return 2
    return 1


def evaluate_audio_quality(stream: StreamMetadata) -> AudioQualityScore:
    """
    Calculates deterministic acoustic fidelity index (AudioQualityScore) for an audio stream.
    Priorities:
    1. Channels (7.1 > 5.1 > 2.0 > 1.0)
    2. Codec Tier (Lossless > E-AC3/AC3/Opus/DTS > AAC > MP3)
    3. Bitrate (nominal kbps)
    Handles missing or null bitrate gracefully without raising exceptions.
    """
    channels = stream.channels if stream.channels and stream.channels > 0 else 2
    sample_rate = stream.sample_rate if stream.sample_rate and stream.sample_rate > 0 else 48000
    bit_rate = stream.bitrate if stream.bitrate and stream.bitrate > 0 else 0
    codec_tier = get_codec_tier(stream.codec)

    bitrate_kbps = bit_rate / 1000.0
    total_score = (
        (channels * 100000.0)
        + (codec_tier * 1000.0)
        + (bitrate_kbps * 0.5)
        + (sample_rate / 100000.0)
    )

    return AudioQualityScore(
        channels=channels,
        sample_rate=sample_rate,
        bit_rate=bit_rate,
        codec_tier=codec_tier,
        total_score=total_score
    )


def _describe_audio_stream(stream: StreamMetadata) -> str:
    """Helper formatting technical summary of audio stream (e.g. '5.1 AC3 640 kbps')."""
    layout = format_channel_layout_label(stream.channels, stream.channel_layout)
    if layout.startswith("Surround "):
        layout_short = layout.replace("Surround ", "")
    elif layout.startswith("Estéreo "):
        layout_short = layout.replace("Estéreo ", "")
    elif layout.startswith("Mono "):
        layout_short = layout.replace("Mono ", "")
    else:
        layout_short = layout

    codec = (stream.codec or "audio").upper()
    if stream.bitrate and stream.bitrate > 0:
        kbps = int(round(stream.bitrate / 1000.0))
        return f"{layout_short} {codec} {kbps} kbps"
    return f"{layout_short} {codec}"


def arbitrate_duplicate_language_streams(
    base_video_streams: List[StreamMetadata],
    external_streams: List[StreamMetadata],
    lang_code: str = "por"
) -> StreamArbitrationResult:
    """
    Arbitrates duplicate language audio streams between base video file and external file.
    If external stream is of higher quality, selects it and marks base language stream for discard.
    If metrics are equal, keeps external stream by default.
    If base stream is equal or superior, notifies user without discarding base stream.
    """
    def _is_target_lang(s: StreamMetadata) -> bool:
        if s.track_type != "audio":
            return False
        lang = (s.language or "").lower()
        title = (s.title or "").lower()
        if lang_code.lower() in PORTUGUESE_TAGS or lang_code.lower() in ("por", "pt"):
            is_tag = lang in PORTUGUESE_TAGS
            is_title = any(kw in title for kw in PORTUGUESE_KEYWORDS)
            return is_tag or is_title
        return lang == lang_code.lower()

    base_pt = [s for s in base_video_streams if _is_target_lang(s)]
    ext_pt = [s for s in external_streams if _is_target_lang(s)]

    # If external stream has no explicit tag, but external file contains audio tracks
    if not ext_pt:
        ext_audios = [s for s in external_streams if s.track_type == "audio"]
        if ext_audios:
            ext_pt = ext_audios

    # Scenario 1: No base PT stream exists (no conflict)
    if not base_pt:
        if ext_pt:
            ext_scored = [(s, evaluate_audio_quality(s)) for s in ext_pt]
            ext_scored.sort(key=lambda x: x[1].total_score, reverse=True)
            chosen = ext_scored[0][0]
            desc = _describe_audio_stream(chosen)
            return StreamArbitrationResult(
                selected_target_audio=chosen,
                discarded_audio_ids=[],
                reason=f"Dublagem externa selecionada ({desc}) sem faixas duplicadas no arquivo base.",
                is_replacement=False
            )
        else:
            audios = [s for s in external_streams + base_video_streams if s.track_type == "audio"]
            fallback = audios[0] if audios else StreamMetadata(
                id=0, codec="unknown", channels=2, sample_rate=48000, fps=0, duration_ms=0, language="por", is_default=True
            )
            return StreamArbitrationResult(
                selected_target_audio=fallback,
                discarded_audio_ids=[],
                reason="Nenhuma faixa identificada com idioma especificado.",
                is_replacement=False
            )

    # Scenario 2: Base PT stream exists, but no external stream provided
    if not ext_pt:
        base_scored = [(s, evaluate_audio_quality(s)) for s in base_pt]
        base_scored.sort(key=lambda x: x[1].total_score, reverse=True)
        chosen = base_scored[0][0]
        desc = _describe_audio_stream(chosen)
        return StreamArbitrationResult(
            selected_target_audio=chosen,
            discarded_audio_ids=[],
            reason=f"Faixa local mantida ({desc}); nenhuma faixa externa fornecida.",
            is_replacement=False
        )

    # Scenario 3: Duplicate language conflict! Compare qualities
    base_scored = [(s, evaluate_audio_quality(s)) for s in base_pt]
    base_scored.sort(key=lambda x: x[1].total_score, reverse=True)
    best_base, best_base_score = base_scored[0]

    ext_scored = [(s, evaluate_audio_quality(s)) for s in ext_pt]
    ext_scored.sort(key=lambda x: x[1].total_score, reverse=True)
    best_ext, best_ext_score = ext_scored[0]

    base_desc = _describe_audio_stream(best_base)
    ext_desc = _describe_audio_stream(best_ext)

    if best_ext_score.total_score > best_base_score.total_score:
        # External is strictly superior -> replacement and discard base PT track(s)
        discard_ids = [s.id for s in base_pt]
        return StreamArbitrationResult(
            selected_target_audio=best_ext,
            discarded_audio_ids=discard_ids,
            reason=f"Dublagem Externa Selecionada: {ext_desc} (Substituindo faixa local: {base_desc} que será descartada)",
            is_replacement=True
        )
    elif best_ext_score.total_score == best_base_score.total_score:
        # Identical metrics -> fallback keeps external track already validated for sync
        discard_ids = [s.id for s in base_pt]
        return StreamArbitrationResult(
            selected_target_audio=best_ext,
            discarded_audio_ids=discard_ids,
            reason=f"Dublagem Externa Selecionada: {ext_desc} (Métricas equivalentes à faixa local: {base_desc} que será descartada)",
            is_replacement=True
        )
    else:
        # Base is superior -> notify user
        return StreamArbitrationResult(
            selected_target_audio=best_base,
            discarded_audio_ids=[],
            reason=f"Faixa local do vídeo ({base_desc}) já possui fidelidade técnica superior à externa ({ext_desc})",
            is_replacement=False
        )


def evaluate_media_streams(file_a: Any, file_b: Any) -> AutoMatchVerdict:
    """
    Executes immediate comparative heuristic evaluation of two media files (MKV, MP4, M4V, MOV),
    producing an AutoMatchVerdict with recommended streams, alternatives, and duplicate language arbitration.
    Supports either file paths (str) or pre-inspected stream lists (List[StreamMetadata]).
    """
    if isinstance(file_a, str):
        streams_a = inspect_media(file_a)
        path_a = file_a
    elif isinstance(file_a, list):
        streams_a = file_a
        path_a = getattr(streams_a[0], "file_path", "file_a") if streams_a else "file_a"
    else:
        raise TypeError(f"file_a must be str or list of StreamMetadata, got {type(file_a)}")

    if isinstance(file_b, str):
        streams_b = inspect_media(file_b)
        path_b = file_b
    elif isinstance(file_b, list):
        streams_b = file_b
        path_b = getattr(streams_b[0], "file_path", "file_b") if streams_b else "file_b"
    else:
        raise TypeError(f"file_b must be str or list of StreamMetadata, got {type(file_b)}")

    all_streams_with_files: List[Tuple[str, StreamMetadata]] = []
    for s in streams_a:
        all_streams_with_files.append((path_a, s))
    for s in streams_b:
        all_streams_with_files.append((path_b, s))

    ranked_videos = rank_video_streams(all_streams_with_files)
    if not ranked_videos:
        raise ValueError("Nenhuma faixa de vídeo válida encontrada em nenhum dos arquivos informados.")

    chosen_video = ranked_videos[0]
    alt_videos = ranked_videos[1:]

    recommended_target, reference_audio, all_audios, is_ambiguous, ambiguity_reason = identify_target_and_ref_audios(
        all_streams_with_files,
        chosen_video.file_path
    )

    # Perform duplicate audio stream arbitration
    base_streams = [s for f, s in all_streams_with_files if f == chosen_video.file_path]
    external_streams = [s for f, s in all_streams_with_files if f != chosen_video.file_path]

    arbitration = arbitrate_duplicate_language_streams(base_streams, external_streams, lang_code="por")

    # If arbitration decided on an external replacement, ensure recommended_target points to it
    if arbitration and arbitration.is_replacement:
        for cand in all_audios:
            if cand.stream.id == arbitration.selected_target_audio.id and cand.file_path != chosen_video.file_path:
                recommended_target = cand
                recommended_target.is_recommended = True
                recommended_target.badge_label = "Dublagem Superior Selecionada"
                break

    alt_audios = [a for a in all_audios if a != recommended_target]

    return AutoMatchVerdict(
        recommended_video=chosen_video,
        alternative_videos=alt_videos,
        recommended_target_audio=recommended_target,
        alternative_audios=alt_audios,
        reference_audio=reference_audio,
        is_ambiguous=is_ambiguous,
        ambiguity_reason=ambiguity_reason,
        arbitration_result=arbitration
    )

