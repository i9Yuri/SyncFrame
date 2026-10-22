"""Media stream inspector using mkvmerge -J and ffprobe."""

import json
import logging
import os
import subprocess
from typing import List, Optional, Tuple, Dict, Any

from .models import StreamMetadata, InspectionResult, StreamCandidate, AutoMatchVerdict

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

        # Estimate bitrate
        bitrate_bps = stream.bitrate or 0
        if bitrate_bps == 0 and os.path.isfile(file_path):
            file_bytes = os.path.getsize(file_path)
            dur_sec = (stream.duration_ms / 1000.0) if stream.duration_ms > 0 else 7200.0
            bitrate_bps = int((file_bytes * 8.0) / dur_sec)

        bitrate_kbps = bitrate_bps / 1000.0

        # Fidelity score
        score = (pixels * 1.0 * codec_wt) + (bitrate_kbps * 50.0)

        res_label = f"{w}x{h}" if w and h else "Resolução Indefinida"
        details = f"{res_label} ({stream.codec}) | ~{bitrate_kbps:.0f} kbps"

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

        # Scoring for Portuguese dub candidate
        score = 0.0
        if is_pt_lang:
            score += 1000.0
        if is_pt_title:
            score += 800.0
        if file_path != chosen_video_file:
            # Strong bonus if coming from the separate dubbed release file
            score += 300.0
        if stream.is_default:
            score += 50.0

        score += (stream.channels or 2) * 20.0
        score += (stream.sample_rate or 48000) / 1000.0

        ch_str = f"{stream.channels}ch" if stream.channels else "2ch"
        lang_str = stream.language.upper() if stream.language else "UND"
        details = f"{lang_str} ({stream.codec}, {ch_str}, {stream.sample_rate}Hz)"

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
        # Fallback: prefer audio from the non-video file
        non_video_audios = [c for c in all_candidates if c.file_path != chosen_video_file]
        recommended_target = non_video_audios[0] if non_video_audios else all_candidates[0]
        recommended_target.is_recommended = False
        recommended_target.badge_label = "Atenção: Seleção Manual Sugerida"
        is_ambiguous = True
        ambiguity_reason = "Nenhuma tag ou título em português encontrada nos metadados. Confirme a faixa manualmente."

    # Identify Reference Audio from the chosen video container
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
        # Fallback reference if no audio in video file
        reference_audio = all_candidates[0]

    return recommended_target, reference_audio, all_candidates, is_ambiguous, ambiguity_reason


def evaluate_media_streams(file_a: str, file_b: str) -> AutoMatchVerdict:
    """
    Executes immediate comparative heuristic evaluation of two MKV media files,
    producing an AutoMatchVerdict with recommended streams and alternatives.
    """
    streams_a = inspect_media(file_a)
    streams_b = inspect_media(file_b)

    all_streams_with_files: List[Tuple[str, StreamMetadata]] = []
    for s in streams_a:
        all_streams_with_files.append((file_a, s))
    for s in streams_b:
        all_streams_with_files.append((file_b, s))

    # 1. Rank video streams
    ranked_videos = rank_video_streams(all_streams_with_files)
    if not ranked_videos:
        raise ValueError("Nenhuma faixa de vídeo válida encontrada em nenhum dos arquivos informados.")

    chosen_video = ranked_videos[0]
    alt_videos = ranked_videos[1:]

    # 2. Identify Target Dubbed Audio and Reference Audio
    recommended_target, reference_audio, all_audios, is_ambiguous, ambiguity_reason = identify_target_and_ref_audios(
        all_streams_with_files,
        chosen_video.file_path
    )

    alt_audios = [a for a in all_audios if a != recommended_target]

    return AutoMatchVerdict(
        recommended_video=chosen_video,
        alternative_videos=alt_videos,
        recommended_target_audio=recommended_target,
        alternative_audios=alt_audios,
        reference_audio=reference_audio,
        is_ambiguous=is_ambiguous,
        ambiguity_reason=ambiguity_reason
    )
