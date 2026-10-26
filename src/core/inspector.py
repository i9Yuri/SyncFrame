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
    StreamArbitrationResult,
    SmartDefaultsConfig,
    ImmersiveAuditResult,
    VideoStreamDetail,
    AudioStreamDetail,
    SubtitleDetail,
    MediaInspectionReport,
    ConsolidatedStreamSelection,
    RemuxJob,
    AudioQualityBadge,
    StreamAuditSummary
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


def sanitize_stream_bitrate(
    raw_bitrate: Optional[int],
    stream_size: int,
    duration_sec: float,
    codec: str,
    channels: int = 2
) -> int:
    """
    Sanitizes audio stream bitrate against physical codec ceilings, eliminating corrupt
    or container-wide bitrates (e.g., 17,697 kbps on an AAC stream).
    Falls back to precise physical byte-rate calculation ((stream_size * 8) / duration_sec)
    or nominal standard codec tables.
    """
    c = (codec or "").lower().replace("-", "").replace("_", "").replace(" ", "")

    ceilings = {
        "aac": 640_000,
        "mp4a": 640_000,
        "ac3": 640_000,
        "eac3": 1_536_000,
        "mp3": 320_000,
        "mp2": 384_000,
        "opus": 510_000,
        "vorbis": 500_000,
        "ogg": 500_000,
        "dts": 1_536_000,
        "flac": 24_576_000,
        "truehd": 24_576_000,
        "dtshd": 24_576_000,
        "pcm": 36_864_000,
    }

    nominals = {
        "aac": 384_000 if channels >= 6 else 192_000,
        "mp4a": 384_000 if channels >= 6 else 192_000,
        "ac3": 640_000 if channels >= 8 else (384_000 if channels >= 6 else 192_000),
        "eac3": 768_000 if channels >= 8 else (640_000 if channels >= 6 else 224_000),
        "mp3": 192_000,
        "opus": 160_000,
        "dts": 768_000,
        "flac": 1_500_000,
        "truehd": 3_500_000,
    }

    ceiling = 640_000
    for k, v in ceilings.items():
        if k in c:
            ceiling = v
            break

    # 1. Check raw_bitrate within theoretical physical limits
    if raw_bitrate is not None and 0 < raw_bitrate <= ceiling:
        return int(raw_bitrate)

    # 2. Fallback to physical stream_size / duration calculation
    if stream_size > 0 and duration_sec > 0:
        est = int(round((stream_size * 8.0) / duration_sec))
        if 0 < est <= ceiling:
            return est

    # 3. Fallback to nominal standard table
    for k, v in nominals.items():
        if k in c:
            return v

    return 192_000


def detect_immersive_audio_metadata(stream_info: dict) -> Tuple[str, bool]:
    """
    Detects immersive/spatial audio metadata (Dolby Atmos, E-AC-3 JOC, TrueHD Atmos,
    multichannel spatial layouts 7.1.4, 7.1, 5.1).
    Returns:
        (descriptive_badge_label, is_immersive_boolean)
    """
    codec = str(stream_info.get("codec_name") or stream_info.get("codec") or "").lower()
    profile = str(stream_info.get("profile") or "").lower()
    layout = str(stream_info.get("channel_layout") or "").lower()
    channels = int(stream_info.get("channels") or 0)
    tags = stream_info.get("tags") or {}
    title = str(tags.get("title") or stream_info.get("title") or "").lower()
    side_data_list = stream_info.get("side_data_list") or []

    # Check for Dolby Atmos or JOC (Joint Object Coding)
    has_atmos = False
    if "atmos" in profile or "joc" in profile or "joint object coding" in profile:
        has_atmos = True
    elif "atmos" in title or "e-ac-3 joc" in title or "eac3 joc" in title or "truehd atmos" in title:
        has_atmos = True
    else:
        for sd in side_data_list:
            sd_type = str(sd.get("side_data_type") or "").lower()
            if "atmos" in sd_type or "joc" in sd_type or "spatial" in sd_type:
                has_atmos = True
                break

    # Spatial layout with height / ceiling channels (e.g. 7.1.4, 5.1.2, 5.1.4, 7.1.2)
    has_height = any(k in layout for k in ("7.1.4", "5.1.2", "5.1.4", "7.1.2", "top", "height"))

    if has_atmos:
        if "7.1.4" in layout:
            return "7.1.4 ATMOS", True
        elif channels == 8 or "7.1" in layout:
            return "7.1 ATMOS", True
        elif channels == 6 or "5.1" in layout:
            return "5.1 ATMOS", True
        elif "truehd" in codec:
            return "TRUEHD ATMOS", True
        return "DOLBY ATMOS", True

    if has_height:
        if "7.1.4" in layout:
            return "7.1.4 SPATIAL", True
        return f"{channels}ch SPATIAL", True

    # High fidelity multichannel Dolby / DTS
    if channels == 8 or "7.1" in layout:
        if any(k in codec for k in ("eac3", "ac3", "truehd", "dolby")):
            return "7.1 DOLBY AUDIO", False
        elif "dts" in codec:
            return "7.1 DTS-HD", False
        return "Surround 7.1", False

    if channels == 6 or "5.1" in layout:
        if any(k in codec for k in ("eac3", "ac3", "truehd", "dolby")):
            return "5.1 DOLBY AUDIO", False
        elif "dts" in codec:
            return "5.1 DTS SURROUND", False
        return "Surround 5.1", False

    if channels == 2 or "stereo" in layout:
        return "Estéreo 2.0", False

    if channels == 1 or "mono" in layout:
        return "Mono 1.0", False

    return format_channel_layout_label(channels, layout), False


def audit_immersive_capabilities(stream: Any) -> ImmersiveAuditResult:
    """
    Evaluates audio stream compatibility and acoustic exploration for 7.1.4 immersive
    soundbars (reference calibration: JBL Bar 1000 MK2 with Dolby Atmos and detachable surrounds).

    Contracts:
        optimal: Full 7.1.4 / Atmos / lossless spatial utilization (7 base + 1 LFE + 4 up-firing height).
        suboptimal: Conventional 5.1 (virtual upmixing), stereo 2.0 (virtualization), or compressed transcode.
    """
    if stream is None:
        return ImmersiveAuditResult(
            status="suboptimal",
            title="JBL Bar 1000: Nenhuma Faixa Selecionada",
            description="Nenhuma faixa de áudio ativa para auditoria multicanal.",
            suggestion="Selecione uma faixa de áudio para auditar a compatibilidade 7.1.4."
        )

    # Unwrap StreamCandidate if passed
    if hasattr(stream, "stream"):
        stream = getattr(stream, "stream")

    if isinstance(stream, dict):
        codec = str(stream.get("codec_name") or stream.get("codec") or "").lower()
        channels = int(stream.get("channels") or 0)
        title = str(stream.get("title") or stream.get("tags", {}).get("title") or "").lower()
        profile = str(stream.get("profile") or "").lower()
        layout = str(stream.get("channel_layout") or "").lower()
        is_immersive = bool(stream.get("is_immersive", False))
        spatial_label = str(stream.get("spatial_label") or "")
        is_suspicious_transcode = bool(stream.get("is_suspicious_transcode", False))
    else:
        codec = str(getattr(stream, "codec", "") or "").lower()
        channels = int(getattr(stream, "channels", 0) or 0)
        title = str(getattr(stream, "title", "") or "").lower()
        profile = str(getattr(stream, "profile", "") or "").lower()
        layout = str(getattr(stream, "channel_layout", "") or "").lower()
        is_immersive = bool(getattr(stream, "is_immersive", False))
        spatial_label = str(getattr(stream, "spatial_label", "") or "")
        is_suspicious_transcode = bool(getattr(stream, "is_suspicious_transcode", False))

    combined_text = f"{codec} {title} {profile} {layout} {spatial_label}".lower()

    # Detect Dolby Atmos or spatial objects
    has_atmos = "atmos" in combined_text or "joc" in combined_text or is_immersive
    has_dtsx = "dts:x" in combined_text or "dts-x" in combined_text
    is_truehd = "truehd" in codec
    is_eac3_joc = ("eac3" in codec or "e-ac-3" in codec) and ("joc" in combined_text or "atmos" in combined_text or is_immersive)
    is_dts_hd_ma_71 = ("dtshd" in codec or "dts-hd" in codec or "dts" in codec) and channels >= 8
    is_lpcm_71 = any(p in codec for p in ("pcm", "flac")) and channels >= 8

    # 1. OPTIMAL_IMMERSIVE (Check Verde)
    if has_atmos or has_dtsx or is_truehd or is_eac3_joc or is_dts_hd_ma_71 or is_lpcm_71 or channels >= 8:
        if has_atmos:
            title_text = "JBL Bar 1000: Atmos 7.1.4 Ativo"
        elif has_dtsx:
            title_text = "JBL Bar 1000: DTS:X 7.1.4 Ativo"
        elif channels >= 8:
            title_text = "JBL Bar 1000: Surround 7.1 Discreto"
        else:
            title_text = "JBL Bar 1000: Imersivo 7.1.4 Ativo"

        return ImmersiveAuditResult(
            status="optimal",
            title=title_text,
            description="Mixagem original com objetos espaciais e canais de altura ativos.",
            suggestion="Aproveitamento acústico máximo em soundbars 7.1.4 e home theaters dedicados."
        )

    # 2. SUBOPTIMAL_ATTENTION (Exclamação Amarela)
    # Cenário 3: Transcodificação Comprimida
    if is_suspicious_transcode or (channels >= 6 and any(k in codec for k in ("aac", "mp4a"))):
        return ImmersiveAuditResult(
            status="suboptimal",
            title="JBL Bar 1000: Multicanal Comprimido",
            description="Transcodificação com compressão de dinâmica e graves atenuados.",
            suggestion="Priorize faixas originais AC-3/E-AC-3 ou TrueHD sem perda."
        )

    # Cenário 1: Multicanal Convencional 5.1
    if channels == 6 or "5.1" in combined_text or any(k in codec for k in ("ac3", "eac3", "dts")):
        return ImmersiveAuditResult(
            status="suboptimal",
            title="JBL Bar 1000: Surround 5.1 Convencional",
            description="Sem canais de teto dedicados; surround operando por emulação.",
            suggestion="Selecione faixa TrueHD/Atmos no seletor ou obtenha release WEB-DL/Remux com áudio E-AC-3 Atmos."
        )

    # Cenário 2: Estéreo / Mono 2.0 ou 1.0
    if channels <= 2:
        title_text = "JBL Bar 1000: Estéreo 2.0 Reduzido" if channels == 2 else "JBL Bar 1000: Áudio Mono 1.0"
        return ImmersiveAuditResult(
            status="suboptimal",
            title=title_text,
            description="Subwoofer e caixas surround operam com emulação estéreo reduzida.",
            suggestion="Selecione faixa multicanal 5.1/7.1 ou fonte de maior fidelidade."
        )

    # Fallback seguro para channels < 8
    return ImmersiveAuditResult(
        status="suboptimal",
        title="JBL Bar 1000: Capacidade Subótima",
        description="Áudio convencional operando sem canais de altura dedicados.",
        suggestion="Recomenda-se release com áudio Dolby Atmos ou DTS:X."
    )


def probe_audio_channels_fast(file_path: str, stream_index: int) -> Tuple[int, str]:
    """
    Fast fallback decode via ffmpeg -i ... -t 1 -af astats -f null -
    to certify physical audio channels and layout if container metadata is missing.
    """
    if not os.path.isfile(file_path):
        return 2, "stereo"
    cmd = [
        "ffmpeg", "-v", "info",
        "-i", file_path,
        "-map", f"0:{stream_index}",
        "-t", "1",
        "-af", "astats",
        "-f", "null",
        "-"
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        stderr = res.stderr or ""
        for line in stderr.splitlines():
            if "Audio:" in line:
                if "5.1" in line:
                    return 6, "5.1(side)"
                elif "7.1" in line:
                    return 8, "7.1"
                elif "stereo" in line:
                    return 2, "stereo"
                elif "mono" in line:
                    return 1, "mono"
            if "Channel count:" in line:
                val = line.split("Channel count:")[-1].strip().split()[0]
                if val.isdigit():
                    ch = int(val)
                    return ch, format_channel_layout_label(ch)
    except Exception as exc:
        logger.debug("Fast probe audio channels fallback failed: %s", exc)
    return 2, "stereo"


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
        is_imm = False
        spatial_lbl = ""
        is_suspicious = False

        if codec_type == "video":
            bitrate_str = s.get("bit_rate") or format_info.get("bit_rate")
            bitrate_int = int(bitrate_str) if bitrate_str and str(bitrate_str).isdigit() else None
        else:
            spatial_lbl, is_imm = detect_immersive_audio_metadata(s)
            if channels <= 0:
                channels, channel_layout = probe_audio_channels_fast(file_path, stream_index)

            stream_size = 0
            for tag_k, tag_v in tags.items():
                if "NUMBER_OF_BYTES" in tag_k.upper():
                    try:
                        stream_size = int(tag_v)
                        break
                    except (ValueError, TypeError):
                        pass

            raw_br = s.get("bit_rate")
            raw_br_int = None
            if raw_br and str(raw_br).isdigit():
                raw_br_int = int(raw_br)
                if "aac" in codec.lower() and raw_br_int > 640_000:
                    is_suspicious = True
            elif "BPS" in tags and str(tags["BPS"]).isdigit():
                raw_br_int = int(tags["BPS"]) * 8
                if "aac" in codec.lower() and raw_br_int > 640_000:
                    is_suspicious = True

            bitrate_int = sanitize_stream_bitrate(
                raw_bitrate=raw_br_int,
                stream_size=stream_size,
                duration_sec=duration_sec,
                codec=codec,
                channels=channels
            )

            audio_profile = AudioProfile(
                codec=codec,
                channels=channels,
                channel_layout=channel_layout,
                sample_rate=sample_rate,
                bit_rate=bitrate_int,
                is_surround=(channels >= 6 or "5.1" in channel_layout or "7.1" in channel_layout),
                is_immersive=is_imm,
                spatial_label=spatial_lbl
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
            container_time_offsets=stream_time_offsets,
            is_immersive=is_imm,
            spatial_label=spatial_lbl,
            is_suspicious_transcode=is_suspicious
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
            is_imm = False
            spatial_lbl = ""
            is_suspicious = False
            bitrate_int = None
            if track_type == "audio":
                raw_bps = props.get("bps") or props.get("bit_rate")
                raw_br = None
                if raw_bps is not None and str(raw_bps).isdigit():
                    raw_br = int(raw_bps) * 8 if "bps" in props else int(raw_bps)
                    if "aac" in codec.lower() and raw_br > 640_000:
                        is_suspicious = True
                dur_sec = container_duration_ms / 1000.0 if container_duration_ms > 0 else 0.0
                stream_size = int(props.get("number_of_bytes", 0)) if str(props.get("number_of_bytes", 0)).isdigit() else 0
                bitrate_int = sanitize_stream_bitrate(raw_br, stream_size, dur_sec, codec, channels=channels)

                ch_layout = f"{channels}.0" if channels in (1, 2) else ("5.1" if channels == 6 else f"{channels}ch")
                spatial_lbl, is_imm = detect_immersive_audio_metadata({
                    "codec": codec,
                    "profile": codec_id,
                    "channel_layout": ch_layout,
                    "channels": channels,
                    "title": title
                })

                audio_profile = AudioProfile(
                    codec=codec,
                    channels=channels,
                    channel_layout=ch_layout,
                    sample_rate=sample_rate,
                    bit_rate=bitrate_int,
                    is_surround=(channels >= 6),
                    is_immersive=is_imm,
                    spatial_label=spatial_lbl
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
                bitrate=bitrate_int,
                width=width_int,
                height=height_int,
                channel_layout=f"{channels}.0" if channels in (1, 2) else ("5.1" if channels == 6 else f"{channels}ch"),
                container_format="mkv",
                audio_profile=audio_profile,
                is_immersive=is_imm,
                spatial_label=spatial_lbl,
                is_suspicious_transcode=is_suspicious
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
                            s.bitrate = ff.bitrate or s.bitrate
                            s.is_immersive = ff.is_immersive
                            s.spatial_label = ff.spatial_label
                            s.is_suspicious_transcode = ff.is_suspicious_transcode
                    elif s.track_type == "audio" and audio_idx < len(ff_audios):
                        ff = ff_audios[audio_idx]
                        s.channel_layout = ff.channel_layout
                        s.audio_profile = ff.audio_profile
                        s.bitrate = ff.bitrate or s.bitrate
                        s.is_immersive = ff.is_immersive
                        s.spatial_label = ff.spatial_label
                        s.is_suspicious_transcode = ff.is_suspicious_transcode
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


def calculate_perceptual_audio_score(stream: StreamMetadata) -> float:
    """
    Computes deterministic perceptual acoustic quality score based on 3 hierarchical tiers:
    Tier 1: Real channel profile (7.1/7.1.4 > 5.1 > 2.0 > 1.0).
    Tier 2: Codec purity and authenticity (Lossless Master: 100 > Broadcast/Cinema AC3/E-AC-3: 80 > Web AAC/MP3: 50).
    Tier 3: Suspicious transcode audit (penalizing dubious inflated AAC web rips).
    """
    channels = stream.channels if stream.channels and stream.channels > 0 else 2
    codec = (stream.codec or "").lower().replace("-", "").replace("_", "").replace(" ", "")

    # Tier 1: Real Channel Profile (dominates completely: 8ch > 6ch > 2ch > 1ch)
    if channels >= 8:
        channel_score = 800_000.0
    elif channels == 6:
        channel_score = 600_000.0
    elif channels == 2:
        channel_score = 200_000.0
    elif channels == 1:
        channel_score = 100_000.0
    else:
        channel_score = channels * 100_000.0

    # Tier 2: Codec Purity & Authenticity
    if any(k in codec for k in ("flac", "truehd", "dtshd", "dtsma", "pcm", "alac", "wav")):
        codec_score = 10_000.0  # Lossless Master (Score 100)
    elif getattr(stream, "is_immersive", False) or "atmos" in (getattr(stream, "spatial_label", "") or "").lower():
        codec_score = 9_000.0   # Broadcast Immersive E-AC-3 JOC / Atmos
    elif any(k in codec for k in ("eac3", "ac3", "dts", "dolby")):
        codec_score = 8_000.0   # Broadcast Nativo / Cinema AC-3 (Score 80)
    elif "opus" in codec:
        codec_score = 7_000.0   # High quality transparent lossy
    elif "aac" in codec:
        codec_score = 5_000.0   # Web transcode lossy (Score 50)
    elif any(k in codec for k in ("mp3", "mp2", "vorbis", "wma")):
        codec_score = 4_000.0   # Legacy lossy (Score 40)
    else:
        codec_score = 1_000.0

    # Tier 3: Suspicious transcode audit & Bitrate
    is_suspicious = getattr(stream, "is_suspicious_transcode", False)
    if "aac" in codec and (is_suspicious or (stream.bitrate and stream.bitrate > 640_000)):
        transcode_penalty = 1_500.0
    else:
        transcode_penalty = 0.0

    # Bitrate tie-breaker (modest scaling, max 80 points)
    bitrate_kbps = (stream.bitrate or 0) / 1000.0
    bitrate_score = min(bitrate_kbps * 0.1, 80.0)

    # Sample rate tie-breaker
    sr = stream.sample_rate if stream.sample_rate and stream.sample_rate > 0 else 48000
    sr_score = min((sr / 100000.0), 10.0)

    return channel_score + codec_score + bitrate_score + sr_score - transcode_penalty


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

    total_score = calculate_perceptual_audio_score(stream)

    return AudioQualityScore(
        channels=channels,
        sample_rate=sample_rate,
        bit_rate=bit_rate,
        codec_tier=codec_tier,
        total_score=total_score
    )


def format_audiophile_recommendation_badge(stream: StreamMetadata) -> Tuple[str, str]:
    """
    Translates raw technical audio specifications (channels, codecs, sample rate, bitrate)
    into an unequivocal, lay-user-friendly recommendation badge and didactic justification.
    Returns:
        (badge_text, didactic_explanation)
    """
    codec = (stream.codec or "").lower()
    channels = stream.channels or 2
    layout = stream.spatial_label or format_channel_layout_label(channels, stream.channel_layout)
    kbps = int(round(stream.bitrate / 1000.0)) if stream.bitrate and stream.bitrate > 0 else 0
    kbps_str = f" {kbps} kbps" if kbps > 0 else ""

    if any(k in codec for k in ("truehd", "flac")) or (codec == "dts" and "lossless" in (stream.title or "").lower()):
        badge = "ÁUDIO DE MAIOR FIDELIDADE"
        didactic = (
            f"Fidelidade Máxima (Lossless): {layout} ({codec.upper()}{kbps_str}) — "
            "Fluxo de estúdio sem perdas (bit-perfect) com preservação total de harmônicos e dinâmica sonora."
        )
    elif stream.is_immersive or "atmos" in (stream.spatial_label or "").lower() or "joc" in codec:
        badge = "MELHOR OPÇÃO RECOMENDADA"
        didactic = (
            f"Recomendado: {layout} ({codec.upper()}{kbps_str}) — "
            "Áudio espacial imersivo com objetos sonoros tridimensionais e máxima faixa dinâmica, "
            "ideal para sistemas home theater e soundbars modernas."
        )
    elif channels >= 6 and any(k in codec for k in ("ac3", "eac3", "dts", "truehd", "flac")):
        badge = "MELHOR OPÇÃO RECOMENDADA"
        codec_name = "Dolby Audio (AC-3)" if "ac3" in codec else codec.upper()
        didactic = (
            f"Recomendado: 5.1 {codec_name}{kbps_str} — "
            f"Faixa de cinema com {channels} canais autênticos e faixa dinâmica superior, "
            "ideal para sistemas home theater e soundbars multicanais."
        )
    elif channels >= 6 and "aac" in codec:
        badge = "ÁUDIO MULTICANAL COMPRIMIDO"
        didactic = (
            f"Faixa 5.1 AAC{kbps_str} — Transcodificação comprimida para streaming web; "
            "pode apresentar menor faixa dinâmica se comparada a transmissões nativas de cinema."
        )
    elif channels == 2:
        badge = "ÁUDIO ESTÉREO OFICIAL"
        didactic = f"Estéreo 2.0 ({codec.upper()}{kbps_str}) — Faixa balanceada para fones de ouvido e alto-falantes convencionais."
    else:
        badge = "ÁUDIO DE MAIOR FIDELIDADE" if channels > 2 else "ÁUDIO PADRÃO"
        didactic = f"{layout} ({codec.upper()}{kbps_str}) — Faixa de áudio convencional."

    return badge, didactic


def format_audiophile_discard_notice(stream: StreamMetadata) -> str:
    """Formats educational explanation of why a competing inferior or transcoded track was superseded."""
    codec = (stream.codec or "").lower()
    channels = stream.channels or 2
    layout = stream.spatial_label or format_channel_layout_label(channels, stream.channel_layout)
    kbps = int(round(stream.bitrate / 1000.0)) if stream.bitrate and stream.bitrate > 0 else 0
    kbps_str = f" ({kbps} kbps)" if kbps > 0 else ""
    return f"Descartada: Faixa {layout} {codec.upper()}{kbps_str} — Transcodificação comprimida com menor fidelidade sonora."


def _describe_audio_stream(stream: StreamMetadata) -> str:
    """Helper formatting technical summary of audio stream (e.g. '5.1 AC-3 384 kbps')."""
    layout = stream.spatial_label or format_channel_layout_label(stream.channels, stream.channel_layout)
    for pfx in ("Surround ", "Estéreo ", "Mono "):
        if layout.startswith(pfx):
            layout = layout.replace(pfx, "")

    codec = (stream.codec or "audio").upper()
    if stream.bitrate and stream.bitrate > 0:
        kbps = int(round(stream.bitrate / 1000.0))
        return f"{layout} {codec} {kbps} kbps"
    return f"{layout} {codec}"


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
        rec_badge, rec_didactic = format_audiophile_recommendation_badge(best_ext)
        discard_notice = format_audiophile_discard_notice(best_base)
        if "ac3" in (best_ext.codec or "").lower() and "aac" in (best_base.codec or "").lower():
            reason_txt = f"{rec_didactic}\n{discard_notice} (Substituindo faixa local: {base_desc} que será descartada; faixa externa selecionada por apresentar áudio multicanal de broadcast autêntico)"
        else:
            reason_txt = f"{rec_didactic}\n{discard_notice} (Substituindo faixa local: {base_desc} que será descartada)"
        return StreamArbitrationResult(
            selected_target_audio=best_ext,
            discarded_audio_ids=discard_ids,
            reason=reason_txt,
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


def evaluate_media_streams(file_a: Any, file_b: Any = None, *extra_files: Any) -> AutoMatchVerdict:
    """
    Executes immediate comparative heuristic evaluation of N media files (MKV, MP4, M4V, MOV, N >= 2),
    producing an AutoMatchVerdict with recommended streams, alternatives, and duplicate language arbitration.
    Supports either file paths (str), list of file paths, or pre-inspected stream lists (List[StreamMetadata]).
    """
    raw_inputs: List[Any] = []
    def _flatten_input(obj: Any):
        if isinstance(obj, (list, tuple)):
            if obj and hasattr(obj[0], "track_type"):
                raw_inputs.append(list(obj))
            else:
                for sub in obj:
                    _flatten_input(sub)
        elif obj is not None:
            raw_inputs.append(obj)

    _flatten_input(file_a)
    if file_b is not None:
        _flatten_input(file_b)
    for extra in extra_files:
        _flatten_input(extra)

    all_streams_with_files: List[Tuple[str, StreamMetadata]] = []
    for idx, item in enumerate(raw_inputs):
        if isinstance(item, str):
            streams = inspect_media(item)
            path = item
        elif isinstance(item, list):
            streams = item
            path = getattr(streams[0], "file_path", f"file_{idx}") if streams else f"file_{idx}"
        else:
            raise TypeError(f"Media input at index {idx} must be str or list of StreamMetadata, got {type(item)}")

        for s in streams:
            all_streams_with_files.append((path, s))

    ranked_videos = rank_video_streams(all_streams_with_files)
    if not ranked_videos:
        raise ValueError("Nenhuma faixa de vídeo válida encontrada em nenhum dos arquivos informados.")

    chosen_video = ranked_videos[0]
    chosen_video.is_best_quality = True
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

    if recommended_target:
        recommended_target.is_best_quality = True
    if reference_audio:
        reference_audio.is_best_quality = True

    # Mark highest quality audio in all_audios
    ranked_sec = rank_secondary_audio_streams(all_audios)
    for cand, is_rec in ranked_sec:
        if is_rec and isinstance(cand, StreamCandidate):
            cand.is_best_quality = True

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


def build_audio_quality_badge(candidate: StreamCandidate, is_best: bool = False) -> AudioQualityBadge:
    """Builds atomic structured AudioQualityBadge from a StreamCandidate."""
    s = candidate.stream
    lang = (s.language or "und").upper()
    brand = s.get_immersive_profile_label()

    if s.is_immersive and s.spatial_label:
        ch_desc = s.spatial_label
    elif s.channel_layout:
        ch_desc = s.channel_layout
    elif s.channels > 0:
        ch_desc = f"{s.channels}.0" if s.channels <= 2 else f"{s.channels - 1}.1"
    else:
        ch_desc = "2.0"

    sr = s.sample_rate if s.sample_rate > 0 else 48000
    br_kbps = int(round(s.bitrate / 1000.0)) if (s.bitrate and s.bitrate > 0) else 0
    codec_name = (s.codec or "").upper()
    filename = os.path.basename(candidate.file_path)

    return AudioQualityBadge(
        language=lang,
        brand_format=brand,
        channels_desc=ch_desc,
        sample_rate_hz=sr,
        bit_rate_kbps=br_kbps,
        codec_name=codec_name,
        source_filename=filename,
        track_id=s.id,
        is_best_option=is_best or candidate.is_best_quality or candidate.is_recommended,
        title=s.title or ""
    )


def build_stream_audit_summary(candidate: StreamCandidate, container_format: str = "mkv") -> StreamAuditSummary:
    """Builds structured deduplicated StreamAuditSummary from a StreamCandidate."""
    s = candidate.stream
    fmt_upper = (container_format or s.container_format or "mkv").lower()
    container_lbl = "MKV Nativo" if fmt_upper == "mkv" else f"{fmt_upper.upper()} -> MKV Remux"

    profile = s.get_immersive_profile_label()

    layout_lbl = format_channel_layout_label(s.channels, s.channel_layout)
    if s.channels >= 6 or "5.1" in layout_lbl or "7.1" in layout_lbl:
        ch_lbl = f"{layout_lbl} Surround"
    elif s.channels == 2:
        ch_lbl = f"{layout_lbl}"
    else:
        ch_lbl = layout_lbl

    codec_lbl = (s.codec or "").upper()
    sr_lbl = f"{s.sample_rate:,} Hz".replace(",", ".") if s.sample_rate > 0 else "48.000 Hz"
    br_lbl = f"{int(round(s.bitrate / 1000.0))} kbps" if (s.bitrate and s.bitrate > 0) else "VBR"

    return StreamAuditSummary(
        container=container_lbl,
        audio_profile=profile,
        channels=ch_lbl,
        codec=codec_lbl,
        sample_rate=sr_lbl,
        bit_rate=br_lbl
    )


def determine_smart_defaults(
    video_stream: StreamMetadata,
    target_audio_stream: StreamMetadata
) -> SmartDefaultsConfig:
    """
    Evaluates video and target audio metadata to dynamically calculate smart defaults:
    1. PAL Cadence Detection (25 fps -> 24 fps):
       If audio has PAL cadence (fps ~25.0, title/tags indicate PAL, or 25 fps audio paired
       with film video at 23.976/24.0 fps), enables pal_pitch_restore by default.
    2. Smart Output Codec Selection:
       - Lossless target (FLAC, TrueHD, PCM, DTS-HD MA): "flac" (Lossless).
       - Multichannel lossy (AC-3, E-AC-3, DTS 5.1/7.1): "eac3" (Surround).
       - Stereo lossy (AAC, MP3, Opus 2.0): "opus" or "aac".
    """
    v_fps = video_stream.fps if video_stream and video_stream.fps > 0 else 23.976
    a_fps = target_audio_stream.fps if target_audio_stream and target_audio_stream.fps > 0 else 0.0
    title_lower = (target_audio_stream.title or "").lower() if target_audio_stream else ""

    is_pal = False
    if (24.8 <= a_fps <= 25.2) and (v_fps <= 24.2):
        is_pal = True
    elif any(k in title_lower for k in ("pal", "25fps", "25 fps", "25.000")):
        is_pal = True

    pal_badge = "[Detectada cadência PAL: Restauração de pitch recomendada]" if is_pal else ""

    codec_lower = (target_audio_stream.codec or "").lower() if target_audio_stream else ""
    channels = target_audio_stream.channels if target_audio_stream else 2

    is_lossless = any(c in codec_lower for c in ("flac", "truehd", "pcm", "alac", "dts-hd", "dtshd", "mlp"))

    if is_lossless:
        selected_codec = "flac"
        reason = "Áudio alvo sem perdas: preservação lossless via FLAC"
    elif channels >= 6 or any(c in codec_lower for c in ("ac3", "eac3", "dts", "surround")):
        selected_codec = "eac3"
        reason = "Áudio multicanal surround: E-AC3 otimizado para preservação espacial"
    else:
        selected_codec = "opus" if ("opus" in codec_lower or "aac" not in codec_lower) else "aac"
        reason = "Áudio estéreo comprimido: codec transparente de alta eficiência"

    return SmartDefaultsConfig(
        pal_pitch_restore=is_pal,
        pal_badge_text=pal_badge,
        target_codec=selected_codec,
        reason=reason
    )


def inspect_single_media(file_path: str) -> MediaInspectionReport:
    """
    Performs deterministic deep inspection of a single media file (.mkv, .mp4, .mov,
    .ac3, .flac, .opus, etc.), extracting container properties, video streams, audio streams,
    subtitles, and chapters via ffprobe.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Media file not found: {file_path}")

    file_name = os.path.basename(file_path)
    file_size_bytes = os.path.getsize(file_path)
    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    is_audio_ext = ext in ("ac3", "eac3", "aac", "dts", "flac", "m4a", "mp3", "wav", "opus")

    base_cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        "-show_chapters",
        "-analyzeduration", "100M",
        "-probesize", "50M",
    ]

    data = None
    try:
        cmd = base_cmd + [file_path]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(res.stdout)
    except Exception as exc:
        logger.warning("Standard ffprobe probing failed for %s (%s). Attempting fallback...", file_path, exc)
        try:
            cmd = base_cmd + ["-err_detect", "ignore_err", file_path]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            data = json.loads(res.stdout)
        except Exception as exc2:
            logger.error("Deep single media inspection failed for %s: %s", file_path, exc2)
            return MediaInspectionReport(
                file_path=file_path,
                file_name=file_name,
                file_size_bytes=file_size_bytes,
                duration_sec=0.0,
                container_format=ext or "unknown",
                is_audio_only=is_audio_ext,
                error_message=f"Falha ao inspecionar o arquivo: {exc2}"
            )

    fmt_info = data.get("format", {})
    container_fmt = fmt_info.get("format_name", ext or "unknown").split(",")[0].strip()
    if ext in ("mkv", "mp4", "m4v", "mov", "flac", "ac3", "aac", "mp3", "opus", "wav", "dts"):
        container_fmt = ext.upper()
    else:
        container_fmt = container_fmt.upper()

    try:
        duration_sec = float(fmt_info.get("duration", 0.0) or 0.0)
    except (ValueError, TypeError):
        duration_sec = 0.0

    video_streams: List[VideoStreamDetail] = []
    audio_streams: List[AudioStreamDetail] = []
    subtitle_streams: List[SubtitleDetail] = []

    for s in data.get("streams", []):
        codec_type = s.get("codec_type", "").lower()
        stream_index = int(s.get("index", 0))
        codec_name = s.get("codec_name", "")
        tags = s.get("tags", {})
        disposition = s.get("disposition", {})

        if codec_type == "video":
            profile = s.get("profile", "")
            width = int(s.get("width", 0) or 0)
            height = int(s.get("height", 0) or 0)
            aspect_ratio = s.get("display_aspect_ratio", "")
            if not aspect_ratio and width > 0 and height > 0:
                aspect_ratio = f"{width}:{height}"

            fps = _parse_fraction(s.get("r_frame_rate", ""))
            if fps == 0.0:
                fps = _parse_fraction(s.get("avg_frame_rate", ""))

            # Bit depth determination
            bit_depth = 8
            bits_per_raw = s.get("bits_per_raw_sample")
            if bits_per_raw and str(bits_per_raw).isdigit():
                bit_depth = int(bits_per_raw)
            else:
                pix_fmt = str(s.get("pix_fmt", "")).lower()
                if "10" in pix_fmt or "p10" in pix_fmt:
                    bit_depth = 10
                elif "12" in pix_fmt or "p12" in pix_fmt:
                    bit_depth = 12

            color_space = s.get("color_space") or s.get("color_primaries") or "bt709"
            color_transfer = str(s.get("color_transfer", "")).lower()
            side_data_str = str(s.get("side_data_list", "")).lower()

            # HDR / Dolby Vision determination
            hdr_format = None
            is_dovi = "dovi" in side_data_str or "dolby vision" in side_data_str
            if "smpte2084" in color_transfer or "hdr10" in color_transfer:
                if "hdr10+" in side_data_str:
                    hdr_format = "HDR10+"
                elif is_dovi:
                    hdr_format = "Dolby Vision / HDR10"
                else:
                    hdr_format = "HDR10"
            elif "arib-std-b67" in color_transfer or "hlg" in color_transfer:
                hdr_format = "HLG"
            elif is_dovi:
                hdr_format = "Dolby Vision"

            video_streams.append(
                VideoStreamDetail(
                    stream_id=stream_index,
                    codec=codec_name,
                    profile=profile,
                    width=width,
                    height=height,
                    aspect_ratio=aspect_ratio,
                    fps=fps,
                    bit_depth=bit_depth,
                    color_space=color_space,
                    hdr_format=hdr_format
                )
            )

        elif codec_type == "audio":
            language = tags.get("language", "und")
            title = tags.get("title", "")
            channels = int(s.get("channels", 0) or 0)
            channel_layout = str(s.get("channel_layout", ""))
            sample_rate = int(s.get("sample_rate", 0) or 0)

            # Bitrate sanitization
            stream_size = 0
            for tag_k, tag_v in tags.items():
                if "NUMBER_OF_BYTES" in tag_k.upper():
                    try:
                        stream_size = int(tag_v)
                        break
                    except (ValueError, TypeError):
                        pass

            raw_br = s.get("bit_rate")
            raw_br_int = int(raw_br) if raw_br and str(raw_br).isdigit() else None
            bit_rate = sanitize_stream_bitrate(
                raw_bitrate=raw_br_int,
                stream_size=stream_size,
                duration_sec=duration_sec,
                codec=codec_name,
                channels=channels
            )

            spatial_lbl, is_imm = detect_immersive_audio_metadata(s)
            audio_streams.append(
                AudioStreamDetail(
                    stream_id=stream_index,
                    language=language,
                    title=title,
                    codec=codec_name,
                    channels=channels,
                    channel_layout=channel_layout,
                    sample_rate=sample_rate,
                    bit_rate=bit_rate,
                    is_immersive=is_imm,
                    immersive_type=spatial_lbl if is_imm else None
                )
            )

        elif codec_type == "subtitle":
            language = tags.get("language", "und")
            title = tags.get("title", "")
            is_forced = bool(disposition.get("forced", 0))
            is_default = bool(disposition.get("default", 0))
            subtitle_streams.append(
                SubtitleDetail(
                    stream_id=stream_index,
                    language=language,
                    title=title,
                    codec=codec_name,
                    is_forced=is_forced,
                    is_default=is_default
                )
            )

    chapters = data.get("chapters", [])
    chapter_count = len(chapters)
    is_audio_only = (len(video_streams) == 0) or is_audio_ext

    return MediaInspectionReport(
        file_path=file_path,
        file_name=file_name,
        file_size_bytes=file_size_bytes,
        duration_sec=duration_sec,
        container_format=container_fmt,
        video_streams=video_streams,
        audio_streams=audio_streams,
        subtitle_streams=subtitle_streams,
        chapter_count=chapter_count,
        is_audio_only=is_audio_only,
        error_message=None
    )


def build_consolidated_selection_state(
    sources: List[str],
    verdict: Optional[AutoMatchVerdict] = None
) -> ConsolidatedStreamSelection:
    """
    Computes consolidated selection state mapping primary video, target dubbed audio,
    and a structured list of secondary audio checkboxes across all ingested sources.
    """
    if len(sources) < 2 and not verdict:
        raise ValueError("build_consolidated_selection_state requires at least 2 sources or a precomputed verdict.")

    if not verdict:
        verdict = evaluate_media_streams(sources[0], sources[1])

    primary_v_file = verdict.recommended_video.file_path
    primary_v_id = verdict.recommended_video.stream.id

    target_a_file = verdict.recommended_target_audio.file_path if verdict.recommended_target_audio else sources[0]
    target_a_id = verdict.recommended_target_audio.stream.id if verdict.recommended_target_audio else 0

    ref_a_file = verdict.reference_audio.file_path if verdict.reference_audio else primary_v_file
    ref_a_id = verdict.reference_audio.stream.id if verdict.reference_audio else None

    # Aggregate all unique audio candidates across verdict
    seen_streams = set()
    all_audio_cands: List[StreamCandidate] = []

    candidates_pool: List[StreamCandidate] = []
    if verdict.recommended_target_audio:
        candidates_pool.append(verdict.recommended_target_audio)
    if verdict.reference_audio:
        candidates_pool.append(verdict.reference_audio)
    candidates_pool.extend(verdict.alternative_audios)

    for cand in candidates_pool:
        key = (cand.file_path, cand.stream.id)
        if key not in seen_streams:
            seen_streams.add(key)
            all_audio_cands.append(cand)

    secondary_selections: List[Tuple[str, int, bool]] = []
    secondary_cands = [
        cand for cand in all_audio_cands
        if not (cand.file_path == target_a_file and cand.stream.id == target_a_id)
    ]

    # Apply smart qualitative ranking to secondary candidates so only the highest fidelity is checked by default
    ranked_secondary = rank_secondary_audio_streams(secondary_cands)
    for cand, is_rec in ranked_secondary:
        secondary_selections.append((cand.file_path, cand.stream.id, is_rec))

    return ConsolidatedStreamSelection(
        primary_video_file=primary_v_file,
        primary_video_track_id=primary_v_id,
        target_audio_file=target_a_file,
        target_audio_track_id=target_a_id,
        secondary_audio_selections=secondary_selections,
        ref_audio_file=ref_a_file,
        ref_audio_track_id=ref_a_id
    )


def apply_selection_to_remux_job(
    selection: ConsolidatedStreamSelection,
    job: RemuxJob
) -> RemuxJob:
    """
    Applies consolidated user stream selections directly to RemuxJob parameters.
    """
    job.video_file = selection.primary_video_file
    job.video_track_id = selection.primary_video_track_id
    job.target_audio_file = selection.target_audio_file
    job.target_track_id = selection.target_audio_track_id
    job.target_audio_track_id = selection.target_audio_track_id
    job.ref_audio_file = selection.ref_audio_file or selection.primary_video_file
    job.ref_audio_track_id = selection.ref_audio_track_id if selection.ref_audio_track_id is not None else 1
    job.secondary_audio_selections = list(selection.secondary_audio_selections)

    has_enabled_secondary = any(enabled for (_, _, enabled) in selection.secondary_audio_selections)
    job.keep_original_audio = has_enabled_secondary

    return job


def compute_stream_quality_score(stream: Any) -> float:
    """
    Computes an acoustic fidelity quality score (0 - 100+) based on the 4-tier model:
    - Tier 1 (Score: 100): TrueHD Atmos, DTS-HD MA 7.1, DTS:X, LPCM 7.1
    - Tier 2 (Score: 80): E-AC-3 JOC (Atmos 5.1/7.1), DTS-HD MA 5.1, DTS 5.1
    - Tier 3 (Score: 65): AC-3 5.1 (Dolby Audio 640/384 kbps)
    - Tier 4 (Score: 40): AAC 2.0, MP3, Opus 2.0
    """
    s = stream.stream if hasattr(stream, "stream") and hasattr(stream.stream, "codec") else stream

    c = str(getattr(s, "codec", "") or "").lower().replace("-", "").replace("_", "")
    layout = str(getattr(s, "channel_layout", "") or "").lower()
    channels = int(getattr(s, "channels", 0) or 0)
    title = str(getattr(s, "title", "") or "").lower()
    is_imm = bool(getattr(s, "is_immersive", False))
    spatial_lbl = str(getattr(s, "spatial_label", "") or "").lower()
    imm_type = str(getattr(s, "immersive_type", "") or "").lower()

    has_atmos = (
        is_imm
        or "atmos" in title
        or "atmos" in layout
        or "atmos" in spatial_lbl
        or "atmos" in imm_type
        or "joc" in layout
        or "joc" in title
    )
    has_dtsx = "dts:x" in title or "dts-x" in title or "dtsx" in title

    # Tier 1: Lossless & Immersive (Base Score: 100)
    if "truehd" in c and has_atmos:
        score = 100.0
    elif has_dtsx:
        score = 99.5
    elif ("dts" in c or "dtshd" in c) and (channels >= 8 or "7.1" in layout or "dts-hd ma" in title):
        score = 99.0
    elif ("truehd" in c or "flac" in c or "pcm" in c) and (channels >= 8 or "7.1" in layout):
        score = 98.5
    elif "truehd" in c or "flac" in c:
        score = 95.0

    # Tier 2: Immersive Broadcast / Multichannel Full (Base Score: 80)
    elif ("eac3" in c or "ec3" in c or "ac3" in c) and has_atmos:
        score = 85.0
    elif ("dts" in c or "dtshd" in c) and (channels >= 6 or "5.1" in layout):
        score = 82.0
    elif "dts" in c:
        score = 80.0

    # Tier 3: Multichannel Conventional (Base Score: 65)
    elif ("ac3" in c or "eac3" in c or "dolby" in c) and (channels >= 6 or "5.1" in layout):
        score = 65.0
    elif channels >= 6 or "5.1" in layout or "7.1" in layout:
        score = 60.0

    # Tier 4: Stereo / Compressed (Base Score: 40)
    elif "opus" in c and channels <= 2:
        score = 45.0
    elif "aac" in c or "mp4a" in c:
        score = 42.0
    elif "mp3" in c:
        score = 38.0
    else:
        score = 40.0

    # Channel bonus: 7.1 (+2.0), 5.1 (+1.0)
    if channels >= 8:
        score += 2.0
    elif channels >= 6:
        score += 1.0

    # Bitrate tie-breaker
    br = getattr(s, "bit_rate", 0) or getattr(s, "bitrate", 0) or 0
    if br and br > 0:
        score += min(1.0, float(br) / 5_000_000.0)

    return score


def rank_secondary_audio_streams(streams: List[Any]) -> List[Tuple[Any, bool]]:
    """
    Ranks non-primary audio streams by qualitative acoustic tier (Lossless/Immersive > Full Surround > AC-3 > Stereo)
    and determines default selection recommendation.
    
    Rule:
    If multiple original language (e.g. English) streams exist (e.g., DTS-HD MA 7.1, TrueHD Atmos 7.1, AC-3 5.1),
    strictly the highest scoring stream (Tier 1 leader) is recommended (True).
    Redundant or lower-tier streams are unchecked (False) by default to prevent container bloat.
    
    Returns:
        List of (stream, is_recommended_checked) tuples ordered from highest to lowest quality.
    """
    if not streams:
        return []

    # Score each stream
    scored_items: List[Tuple[float, Any]] = []
    for st in streams:
        sc = compute_stream_quality_score(st)
        scored_items.append((sc, st))

    # Sort descending by score
    scored_items.sort(key=lambda x: x[0], reverse=True)

    # Identify original / English language tracks
    def _is_original_lang(st: Any) -> bool:
        s = st.stream if hasattr(st, "stream") and hasattr(st.stream, "language") else st
        lang = str(getattr(s, "language", "") or "").lower()
        title = str(getattr(s, "title", "") or "").lower()
        return (
            "eng" in lang
            or "en" in lang
            or "english" in lang
            or "inglês" in lang
            or "ingles" in lang
            or "original" in title
            or lang in ("und", "")
        )

    # Find the single highest-scoring stream to check by default
    orig_candidates = [item for item in scored_items if _is_original_lang(item[1])]
    best_target = orig_candidates[0][1] if orig_candidates else (scored_items[0][1] if scored_items else None)

    results: List[Tuple[Any, bool]] = []
    for sc, item in scored_items:
        is_recommended = (item is best_target)
        results.append((item, is_recommended))

    return results


class Inspector:
    """Namespace wrapper for media inspection and stream ranking routines."""
    rank_secondary_audio_streams = staticmethod(rank_secondary_audio_streams)
    compute_stream_quality_score = staticmethod(compute_stream_quality_score)
    inspect_media = staticmethod(inspect_media)
    probe_media_file = staticmethod(probe_media_file)
    inspect_single_media = staticmethod(inspect_single_media)
    detect_immersive_audio_metadata = staticmethod(detect_immersive_audio_metadata)
    audit_immersive_capabilities = staticmethod(audit_immersive_capabilities)
    evaluate_media_streams = staticmethod(evaluate_media_streams)
    arbitrate_duplicate_language_streams = staticmethod(arbitrate_duplicate_language_streams)
    build_consolidated_selection_state = staticmethod(build_consolidated_selection_state)
    apply_selection_to_remux_job = staticmethod(apply_selection_to_remux_job)
    build_audio_quality_badge = staticmethod(build_audio_quality_badge)
    build_stream_audit_summary = staticmethod(build_stream_audit_summary)




