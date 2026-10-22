"""SyncFrame Core Processing Engine."""

from .models import StreamMetadata, InspectionResult, SyncMetrics, RemuxJob
from .inspector import inspect_media, get_inspection_result
from .extractor import extract_reference_channel
from .correlator import compute_acoustic_correlation
from .transformer import apply_temporal_transform
from .remuxer import execute_lossless_remux
from .temp_manager import TempWorkspace
from .disk_utils import check_disk_space

__all__ = [
    "StreamMetadata",
    "InspectionResult",
    "SyncMetrics",
    "RemuxJob",
    "inspect_media",
    "get_inspection_result",
    "extract_reference_channel",
    "compute_acoustic_correlation",
    "apply_temporal_transform",
    "execute_lossless_remux",
    "TempWorkspace",
    "check_disk_space",
]
