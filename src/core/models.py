"""Data models and contract schemas for SyncFrame."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any


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

    def display_label(self) -> str:
        """User-friendly label for stream selection in GUI dropdowns."""
        lang = self.language.upper() if self.language else "UND"
        default_tag = " [Padrão]" if self.is_default else ""
        if self.track_type == "video":
            res = f"{self.width}x{self.height}" if self.width and self.height else ""
            fps_str = f"{self.fps:.3f} fps" if self.fps > 0 else ""
            details = ", ".join(filter(None, [self.codec, res, fps_str]))
            return f"Vídeo #{self.id}: {details}{default_tag}"
        else:
            ch_str = f"{self.channels}ch" if self.channels > 0 else ""
            sr_str = f"{self.sample_rate}Hz" if self.sample_rate > 0 else ""
            title_str = f" - {self.title}" if self.title else ""
            details = ", ".join(filter(None, [self.codec, ch_str, sr_str]))
            return f"Áudio #{self.id} ({lang}): {details}{title_str}{default_tag}"


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
    correlation_curve: List[float] = field(default_factory=list)  # Visual preview of cross-correlation peak

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
