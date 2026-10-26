import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any, Literal


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


def format_immersive_profile_label(
    codec: str,
    channels: int,
    channel_layout: str = "",
    is_immersive: bool = False,
    title: str = "",
    spatial_label: str = ""
) -> str:
    """
    Standardized badge profile for channel audit and stream selection:
    DOLBY ATMOS, DOLBY AUDIO 5.1, DTS-HD MA 7.1, DTS SURROUND, ESTÉREO CONVENCIONAL.
    """
    c = (codec or "").lower().replace("-", "").replace("_", "")
    layout_lower = (channel_layout or "").lower()
    title_lower = (title or "").lower()
    spatial_lower = (spatial_label or "").lower()

    if is_immersive or "atmos" in title_lower or "atmos" in layout_lower or "atmos" in spatial_lower or "joc" in layout_lower:
        return "DOLBY ATMOS"

    if "dts" in c or "dts" in title_lower:
        if channels >= 8 or "7.1" in layout_lower or "dts-hd ma" in title_lower or "dtshd" in c:
            return "DTS-HD MA 7.1"
        elif "dts-hd" in title_lower or "dtshd" in c:
            return f"DTS-HD MA {channels}.1" if channels >= 6 else "DTS-HD MA"
        return "DTS SURROUND"

    if any(k in c for k in ("ac3", "eac3", "truehd", "dolby")) or "dolby" in title_lower:
        if channels >= 8 or "7.1" in layout_lower:
            return "DOLBY AUDIO 7.1"
        elif channels >= 6 or "5.1" in layout_lower:
            return "DOLBY AUDIO 5.1"
        elif channels == 2 and ("surround" in layout_lower or "surround" in title_lower):
            return "DOLBY SURROUND"
        elif channels <= 2:
            return "ESTÉREO CONVENCIONAL"
        return f"DOLBY AUDIO {channels}ch"

    if channels <= 2:
        return "ESTÉREO CONVENCIONAL"
    elif channels >= 8 or "7.1" in layout_lower:
        return "SURROUND 7.1"
    elif channels >= 6 or "5.1" in layout_lower:
        return "SURROUND 5.1"

    return format_channel_layout_label(channels, channel_layout).upper()



@dataclass
class AudioProfile:
    """Detailed acoustic and channel metrics for an audio stream."""
    codec: str
    channels: int
    channel_layout: str
    sample_rate: int
    bit_rate: Optional[int] = None
    is_surround: bool = False
    is_immersive: bool = False
    spatial_label: str = ""

    def layout_label(self) -> str:
        if self.is_immersive and self.spatial_label:
            return self.spatial_label
        return format_channel_layout_label(self.channels, self.channel_layout)

    def spec_label(self) -> str:
        parts = [self.codec.upper()]
        if self.sample_rate > 0:
            parts.append(f"{self.sample_rate:,} Hz".replace(",", "."))
        if self.bit_rate and self.bit_rate > 0:
            kbps = int(round(self.bit_rate / 1000.0))
            parts.append(f"{kbps} kbps")
        if self.spatial_label:
            parts.append(self.spatial_label)
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
    container_time_offsets: Optional["ContainerTimeOffsets"] = None
    is_immersive: bool = False
    spatial_label: str = ""
    is_suspicious_transcode: bool = False

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
            layout_lbl = self.spatial_label or (format_channel_layout_label(self.channels, self.channel_layout) if self.channels > 0 else "")
            if layout_lbl:
                ch_str = f"{self.channels}ch ({layout_lbl})"
            sr_str = f"{self.sample_rate}Hz" if self.sample_rate > 0 else ""
            title_str = f" - {self.title}" if self.title else ""
            details = ", ".join(filter(None, [self.codec.upper(), ch_str, sr_str]))
            return f"Áudio #{self.id} ({lang}): {details}{title_str}{default_tag}"

    def get_immersive_profile_label(self) -> str:
        return format_immersive_profile_label(
            codec=self.codec,
            channels=self.channels,
            channel_layout=self.channel_layout,
            is_immersive=self.is_immersive,
            title=self.title,
            spatial_label=self.spatial_label
        )


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
    container_time_offsets: Optional["ContainerTimeOffsets"] = None


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
class ContainerTimeOffsets:
    """Probed container timestamp offsets from format/stream headers and edit lists (elst)."""
    format_start_time_ms: float = 0.0
    stream_start_time_ms: float = 0.0
    edit_list_offset_ms: float = 0.0
    net_adjustment_ms: float = 0.0

    @property
    def total_pts_start_ms(self) -> float:
        """Effective presentation start time in ms considering format/stream start and edit list."""
        # When edit list specifies initial delay, or stream start_time is set
        base_start = self.stream_start_time_ms if self.stream_start_time_ms != 0.0 else self.format_start_time_ms
        return base_start + self.edit_list_offset_ms


@dataclass
class DiscontinuityReport:
    """Report on non-linear step discontinuities (montage cuts, opening gaps, distributor logos)."""
    has_cuts: bool = False
    step_delta_ms: float = 0.0
    estimated_split_timestamp_sec: Optional[float] = None
    confidence: float = 0.0
    diagnosis: str = "Linearidade temporal preservada (sem cortes detectados)"
    window_offsets: List[Tuple[float, float, float]] = field(default_factory=list)


@dataclass
class AuditVerificationResult:
    """Closed-loop post-remux acoustic verification result comparing output MKV to reference."""
    passed: bool
    residual_offset_ms: float
    verified_sr: int = 48000
    verified_channels: int = 2
    error_message: str = ""
    is_fatal: bool = False


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
    pslr_score: float = 0.0
    discontinuity_report: Optional[DiscontinuityReport] = None
    net_offset_ms: float = 0.0

    @property
    def is_confident(self) -> bool:
        """Determines if the correlation peak meets the statistical threshold (confidence >= 0.45 or score >= 0.35 and pslr >= 3.5)."""
        if self.pslr_score > 0:
            return self.confidence_score >= 0.45 and self.pslr_score >= 3.5
        return self.confidence_score >= 0.35


@dataclass
class AudioQualityScore:
    """Quantitative acoustic fidelity index for stream quality ranking."""
    channels: int
    sample_rate: int
    bit_rate: int
    codec_tier: int
    total_score: float


@dataclass
class StreamArbitrationResult:
    """Verdict of audio stream quality comparison and duplicate language replacement."""
    selected_target_audio: StreamMetadata
    discarded_audio_ids: List[int]
    reason: str
    is_replacement: bool


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
    pal_pitch_restore: bool = False
    audio_codec: str = "flac"  # "flac", "opus", "eac3", "aac"
    run_post_audit: bool = True
    discarded_audio_ids: List[int] = field(default_factory=list)
    secondary_audio_selections: List[Tuple[str, int, bool]] = field(default_factory=list)
    target_audio_track_id: Optional[int] = None
    ref_audio_file: Optional[str] = None

    def __post_init__(self):
        if self.target_audio_track_id is not None:
            self.target_track_id = self.target_audio_track_id
        else:
            self.target_audio_track_id = self.target_track_id
        if self.ref_audio_file is None:
            self.ref_audio_file = self.video_file


@dataclass
class StreamReviewState:
    """State contract representing selected tracks and custom options in the Review Gate."""
    selected_video_id: int
    selected_target_audio_id: int
    selected_ref_audio_id: int
    pal_restore_enabled: bool
    target_codec: str
    is_customized: bool = False


@dataclass
class SmartDefaultsConfig:
    """Dynamic configuration calculated from video and audio streams for PAL and codec selection."""
    pal_pitch_restore: bool
    pal_badge_text: str
    target_codec: str
    reason: str


@dataclass
class StreamCandidate:
    """A scored stream candidate from one of the examined media files."""
    stream: StreamMetadata
    file_path: str
    score: float = 0.0
    is_recommended: bool = False
    badge_label: str = ""
    details_str: str = ""
    is_best_quality: bool = False

    def summary_title(self) -> str:
        basename = os.path.basename(self.file_path)
        fmt = self.stream.container_format.upper() if self.stream.container_format else "MKV"
        if self.stream.track_type == "video":
            res = f"{self.stream.width}x{self.stream.height}" if self.stream.width and self.stream.height else "Vídeo"
            fps_str = f" @ {self.stream.fps:.3f}fps" if self.stream.fps > 0 else ""
            return f"[{res}{fps_str}] {self.stream.codec.upper()} [{fmt}] — {basename} (Trilha #{self.stream.id})"
        else:
            lang = self.stream.language.upper() if self.stream.language else "UND"
            layout_tag = self.stream.spatial_label or (format_channel_layout_label(self.stream.channels, self.stream.channel_layout) if self.stream.channels else "")
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
    arbitration_result: Optional[StreamArbitrationResult] = None


@dataclass
class MediaSourceInfo:
    """Represents high-level presentation information for an ingested media file."""
    file_path: str
    file_size_formatted: str = ""
    extension: str = ""
    role_label: str = ""
    summary: str = ""
    is_video_source: bool = False


@dataclass
class ImmersiveAuditResult:
    """Compatibility audit result for immersive 7.1.4 soundbars (e.g. JBL Bar 1000 MK2)."""
    status: Literal["optimal", "suboptimal"]
    title: str
    description: str
    suggestion: str


@dataclass
class VideoStreamDetail:
    """Detailed visual stream attributes for single media inspection."""
    stream_id: int
    codec: str
    profile: str
    width: int
    height: int
    aspect_ratio: str
    fps: float
    bit_depth: int
    color_space: str
    hdr_format: Optional[str] = None


@dataclass
class AudioStreamDetail:
    """Detailed acoustic stream attributes for single media inspection."""
    stream_id: int = 0
    language: str = ""
    title: str = ""
    codec: str = ""
    channels: int = 2
    channel_layout: str = ""
    sample_rate: int = 48000
    bit_rate: int = 0
    is_immersive: bool = False
    immersive_type: Optional[str] = None
    spatial_label: str = ""
    container_format: str = "mkv"

    def __init__(
        self,
        stream_id: int = 0,
        language: str = "",
        title: str = "",
        codec: str = "",
        channels: int = 2,
        channel_layout: str = "",
        sample_rate: int = 48000,
        bit_rate: int = 0,
        is_immersive: bool = False,
        immersive_type: Optional[str] = None,
        spatial_label: str = "",
        container_format: str = "mkv",
        id: Optional[int] = None,
        bitrate: Optional[int] = None,
        **kwargs
    ):
        self.stream_id = stream_id if id is None else id
        self.language = language
        self.title = title
        self.codec = codec
        self.channels = channels
        self.channel_layout = channel_layout
        self.sample_rate = sample_rate
        self.bit_rate = bit_rate if bitrate is None else bitrate
        self.is_immersive = is_immersive
        self.immersive_type = immersive_type
        self.spatial_label = spatial_label
        self.container_format = container_format

    @property
    def id(self) -> int:
        return self.stream_id

    @id.setter
    def id(self, val: int) -> None:
        self.stream_id = val

    @property
    def bitrate(self) -> int:
        return self.bit_rate

    @bitrate.setter
    def bitrate(self, val: int) -> None:
        self.bit_rate = val

    def get_immersive_profile_label(self) -> str:
        return format_immersive_profile_label(
            codec=self.codec,
            channels=self.channels,
            channel_layout=self.channel_layout,
            is_immersive=self.is_immersive,
            title=self.title,
            spatial_label=self.spatial_label or self.immersive_type or ""
        )


@dataclass
class SubtitleDetail:
    """Subtitle stream attributes for single media inspection."""
    stream_id: int
    language: str
    title: str
    codec: str
    is_forced: bool = False
    is_default: bool = False


@dataclass
class MediaInspectionReport:
    """Deep structural inspection report for a single ingested media file."""
    file_path: str
    file_name: str
    file_size_bytes: int
    duration_sec: float
    container_format: str
    video_streams: List[VideoStreamDetail] = field(default_factory=list)
    audio_streams: List[AudioStreamDetail] = field(default_factory=list)
    subtitle_streams: List[SubtitleDetail] = field(default_factory=list)
    chapter_count: int = 0
    is_audio_only: bool = False
    error_message: Optional[str] = None


@dataclass
class ConsolidatedStreamSelection:
    """State contract representing explicit user choices in the dual-dropdown and multi-checkbox Review Gate."""
    primary_video_file: str
    primary_video_track_id: int
    target_audio_file: str
    target_audio_track_id: int
    secondary_audio_selections: List[Tuple[str, int, bool]] = field(default_factory=list)
    ref_audio_file: Optional[str] = None
    ref_audio_track_id: Optional[int] = None


@dataclass
class AudioQualityBadge:
    """Dataclass structured for atomic chip rendering of secondary audio streams."""
    language: str  # e.g., "ENG", "POR", "JAP"
    brand_format: str  # e.g., "DOLBY ATMOS", "DOLBY AUDIO", "DTS-HD MA", "DTS", "PCM"
    channels_desc: str  # e.g., "7.1.4", "7.1", "5.1", "2.0"
    sample_rate_hz: int  # e.g., 48000
    bit_rate_kbps: int  # e.g., 640 or 0
    codec_name: str  # e.g., "TRUEHD", "E-AC-3", "AC-3", "DTS", "FLAC"
    source_filename: str  # e.g., "Vingadores...mkv"
    track_id: int  # e.g., 2
    is_best_option: bool = False
    title: str = ""


@dataclass
class StreamAuditSummary:
    """Structured deduplicated metrics for the channel audit bar."""
    container: str  # e.g., "MKV Nativo", "MP4 -> MKV Remux"
    audio_profile: str  # e.g., "DOLBY ATMOS", "DOLBY AUDIO 5.1", "DTS-HD MA 7.1", "ESTÉREO CONVENCIONAL"
    channels: str  # e.g., "7.1.4 Surround", "5.1 Surround", "2.0 Estéreo"
    codec: str  # e.g., "E-AC-3", "AC-3", "TrueHD", "DTS", "FLAC"
    sample_rate: str  # e.g., "48.000 Hz"
    bit_rate: str  # e.g., "640 kbps"




