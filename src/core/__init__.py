"""SyncFrame Core Processing Engine."""

from .models import (
    StreamMetadata,
    InspectionResult,
    SyncMetrics,
    RemuxJob,
    StreamCandidate,
    AutoMatchVerdict,
    AudioQualityScore,
    StreamArbitrationResult,
    MediaSourceInfo
)
from .inspector import (
    inspect_media,
    get_inspection_result,
    rank_video_streams,
    identify_target_and_ref_audios,
    evaluate_media_streams,
    evaluate_audio_quality,
    arbitrate_duplicate_language_streams,
    get_codec_tier
)
from .extractor import extract_reference_channel
from .correlator import compute_acoustic_correlation
from .transformer import apply_temporal_transform
from .remuxer import execute_lossless_remux, build_mkvmerge_exclusion_flags, build_mkvmerge_hybrid_command
from .temp_manager import TempWorkspace
from .disk_utils import check_disk_space

__all__ = [
    "StreamMetadata",
    "InspectionResult",
    "SyncMetrics",
    "RemuxJob",
    "StreamCandidate",
    "AutoMatchVerdict",
    "AudioQualityScore",
    "StreamArbitrationResult",
    "MediaSourceInfo",
    "inspect_media",
    "get_inspection_result",
    "rank_video_streams",
    "identify_target_and_ref_audios",
    "evaluate_media_streams",
    "evaluate_audio_quality",
    "arbitrate_duplicate_language_streams",
    "get_codec_tier",
    "extract_reference_channel",
    "compute_acoustic_correlation",
    "apply_temporal_transform",
    "execute_lossless_remux",
    "build_mkvmerge_exclusion_flags",
    "build_mkvmerge_hybrid_command",
    "TempWorkspace",
    "check_disk_space",
]

