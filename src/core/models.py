import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any


def format_channel_layout_label(channels: int, layout: str = "") -> str:
    """
    Returns standardized user-facing technical label for audio channel layout
    (e.g., 'Mono 1.0', 'Estéreo 2.0', 'Surround 5.1', 'Surround 7.1').
    """
    layout_lower = (layout or "").lower().replace(" ", "").replace("(side)", "").replace("(back)", "")
    if channels == 1 or layout_lower == "mono":
        return "Mono 1.0"
    elif channels == 2 or layout_lower == "stereo":
        return "Estéreo 2.0"
    elif channels == 6 or "5.1" in layout_lower:
        return "Surround 5.1"
    elif channels == 8 or "7.1" in layout_lower:
        return "Surround 7.1"
    elif channels > 0:
        return f"{channels} Canais"
    return "Canais Desconhecidos"


@dataclass
class AudioProfile:
    """Detailed acoustic and channel metrics for an audio stream."""
    codec: str
    channels: int
    channel_layout: str
    sample_rate: int
    bit_rate: Optional[int] = None
    is_surround: bool = False

    def layout_label(self) -> str:
        return format_channel_layout_label(self.channels, self.channel_layout)

    def spec_label(self) -> str:
        parts = [self.codec.upper()]
        if self.sample_rate > 0:
            parts.append(f"{self.sample_rate:,} Hz".replace(",", "."))
        if self.bit_rate and self.bit_rate > 0:
            kbps = int(round(self.bit_rate / 1000.0))
            parts.append(f"{kbps} kbps")
        return " • ".join(parts)


@dataclass
class StreamMetadata:
    """Represents metadata for a single video or audio stream in a media container."""
    id: int
    codec: str
    channels: int
    sample_rate: int
    fps: float
    duration_ms: float
    language: str
    is_default: bool
    track_type: str = "audio"  # "video" or "audio" or "subtitles"
    title: str = ""
    codec_id: str = ""
    bitrate: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    channel_layout: str = ""
    container_format: str = "mkv"
    audio_profile: Optional[AudioProfile] = None

    def display_label(self) -> str:
        """User-friendly label for stream selection in GUI dropdowns."""
        lang = self.language.upper() if self.language else "UND"
        default_tag = " [Padrão]" if self.is_default else ""
        if self.track_type == "video":
            res = f"{self.width}x{self.height}" if self.width and self.height else ""
            fps_str = f"{self.fps:.3f} fps" if self.fps > 0 else ""
            details = ", ".join(filter(None, [self.codec.upper(), res, fps_str]))
            return f"Vídeo #{self.id}: {details}{default_tag}"
        else:
            ch_str = f"{self.channels}ch" if self.channels > 0 else ""
            if self.channels > 0 and self.channel_layout:
                layout_lbl = format_channel_layout_label(self.channels, self.channel_layout)
                ch_str = f"{self.channels}ch ({layout_lbl})"
            sr_str = f"{self.sample_rate}Hz" if self.sample_rate > 0 else ""
            title_str = f" - {self.title}" if self.title else ""
            details = ", ".join(filter(None, [self.codec.upper(), ch_str, sr_str]))
            return f"Áudio #{self.id} ({lang}): {details}{title_str}{default_tag}"


@dataclass
class MediaContainerInfo:
    """Probed container information for MKV, MP4, M4V, or MOV files."""
    file_path: str
    container_format: str  # "mkv", "mp4", "mov", "m4v"
    duration_ms: float
    video_streams: List[StreamMetadata] = field(default_factory=list)
    audio_streams: List[StreamMetadata] = field(default_factory=list)
    all_streams: List[StreamMetadata] = field(default_factory=list)
    is_corrupted: bool = False


@dataclass
class ExtractedAudioResult:
    """Result of direct-stream demuxing or fallback conversion."""
    output_path: str
    codec: str
    is_direct_copy: bool
    channels: int
    sample_rate: int


@dataclass
class InspectionResult:
    """Result of analyzing both video source container and audio source container."""
    video_source: str
    audio_source: str
    selected_video_stream: Optional[StreamMetadata] = None
    ref_audio_stream: Optional[StreamMetadata] = None
    target_audio_stream: Optional[StreamMetadata] = None
    all_video_streams: List[StreamMetadata] = field(default_factory=list)
    all_audio_streams_video: List[StreamMetadata] = field(default_factory=list)
    all_audio_streams_audio: List[StreamMetadata] = field(default_factory=list)


@dataclass
class SyncMetrics:
    """Mathematical alignment metrics computed via FFT acoustic cross-correlation."""
    static_offset_ms: float
    drift_ratio: float
    confidence_score: float
    detected_fps_mismatch: bool
    time_stretch_ratio: float = 1.0
    fps_diagnosis: str = "Taxas de quadros congruentes (sem deriva contínua)"
    offsets_by_window: List[Tuple[float, float, float]] = field(default_factory=list)
    correlation_curve: List[float] = field(default_factory=list)

    @property
    def is_confident(self) -> bool:
        """Determines if the correlation peak meets the statistical threshold (> 0.35)."""
        return self.confidence_score >= 0.35


@dataclass
class RemuxJob:
    """Parameters required to execute a lossless remux using mkvmerge."""
    output_path: str
    video_file: str
    target_audio_file: str
    offset_ms: float
    stretch_ratio: float
    keep_original_audio: bool
    target_track_id: int = 0
    ref_audio_track_id: int = 1
    video_track_id: int = 0
    target_audio_language: str = "por"
    target_audio_name: str = "Português (Brasil)"
    original_audio_language: str = "eng"
    original_audio_name: str = "Áudio Original"


@dataclass
class StreamCandidate:
    """A scored stream candidate from one of the examined media files."""
    stream: StreamMetadata
    file_path: str
    score: float = 0.0
    is_recommended: bool = False
    badge_label: str = ""
    details_str: str = ""

    def summary_title(self) -> str:
        basename = os.path.basename(self.file_path)
        fmt = self.stream.container_format.upper() if self.stream.container_format else "MKV"
        if self.stream.track_type == "video":
            res = f"{self.stream.width}x{self.stream.height}" if self.stream.width and self.stream.height else "Vídeo"
            fps_str = f" @ {self.stream.fps:.3f}fps" if self.stream.fps > 0 else ""
            return f"[{res}{fps_str}] {self.stream.codec.upper()} [{fmt}] — {basename} (Trilha #{self.stream.id})"
        else:
            lang = self.stream.language.upper() if self.stream.language else "UND"
            layout_tag = format_channel_layout_label(self.stream.channels, self.stream.channel_layout) if self.stream.channels else ""
            title = f" ({self.stream.title})" if self.stream.title else ""
            specs = " • ".join(filter(None, [self.stream.codec.upper(), layout_tag]))
            return f"[{lang}] {specs}{title} [{fmt}] — {basename} (Trilha #{self.stream.id})"


@dataclass
class AutoMatchVerdict:
    """Result of deterministic comparative heuristic ranking between two media containers."""
    recommended_video: StreamCandidate
    alternative_videos: List[StreamCandidate] = field(default_factory=list)
    recommended_target_audio: Optional[StreamCandidate] = None
    alternative_audios: List[StreamCandidate] = field(default_factory=list)
    reference_audio: Optional[StreamCandidate] = None
    is_ambiguous: bool = False
    ambiguity_reason: str = ""
