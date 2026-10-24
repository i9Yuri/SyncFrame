"""Stream Review Gate component wrapper and contract re-exports."""

from ...core.models import StreamReviewState, SmartDefaultsConfig
from ...core.inspector import determine_smart_defaults
from .unified_drop_zone import (
    UnifiedDropZone,
    install_wheel_blocker,
    NoWheelComboBox,
    WheelBlockerFilter,
)

# Semantic alias for UnifiedDropZone acting as the Review Gate
StreamReviewGate = UnifiedDropZone

__all__ = [
    "StreamReviewGate",
    "UnifiedDropZone",
    "StreamReviewState",
    "SmartDefaultsConfig",
    "determine_smart_defaults",
    "install_wheel_blocker",
    "NoWheelComboBox",
    "WheelBlockerFilter",
]
