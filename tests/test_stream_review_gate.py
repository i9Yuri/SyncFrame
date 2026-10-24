"""Unit tests for StreamReviewGate, wheel blocker, smart defaults, and review state machine."""

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication, QComboBox

from src.core.models import (
    RemuxJob,
    StreamCandidate,
    StreamMetadata,
    StreamReviewState,
    SmartDefaultsConfig,
    AutoMatchVerdict,
)
from src.core.inspector import determine_smart_defaults
from src.ui.components.stream_review_gate import (
    StreamReviewGate,
    UnifiedDropZone,
    install_wheel_blocker,
    NoWheelComboBox,
)
from src.ui.workers import UnifiedPipelineWorker

app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)


def make_metadata(
    id: int,
    codec: str,
    channels: int,
    sample_rate: int,
    fps: float,
    duration_ms: float,
    language: str = "und",
    is_default: bool = False,
    track_type: str = "audio",
    title: str = "",
    width: int = 0,
    height: int = 0,
    channel_layout: str = "",
    container_format: str = "mkv"
) -> StreamMetadata:
    return StreamMetadata(
        id=id,
        codec=codec,
        channels=channels,
        sample_rate=sample_rate,
        fps=fps,
        duration_ms=duration_ms,
        language=language,
        is_default=is_default,
        track_type=track_type,
        title=title,
        width=width,
        height=height,
        channel_layout=channel_layout,
        container_format=container_format
    )


class TestStreamReviewGate(unittest.TestCase):
    """Validates StreamReviewGate component, wheel blockers, smart defaults, and state handling."""

    def test_gate_alias_and_exports(self):
        """Verifies StreamReviewGate is an alias of UnifiedDropZone."""
        self.assertIs(StreamReviewGate, UnifiedDropZone)

    def test_wheel_blocker_installation(self):
        """Ensures install_wheel_blocker blocks wheel events on QComboBox."""
        cb = QComboBox()
        cb.addItem("Item 1")
        cb.addItem("Item 2")
        install_wheel_blocker(cb)

        wheel_ev = QWheelEvent(
            QPoint(10, 10),
            QPoint(10, 10),
            QPoint(0, 120),
            QPoint(0, 120),
            Qt.NoButton,
            Qt.NoModifier,
            Qt.ScrollUpdate,
            False
        )
        cb.wheelEvent(wheel_ev)
        self.assertFalse(wheel_ev.isAccepted())
        cb.deleteLater()

    def test_no_wheel_combobox(self):
        """Verifies NoWheelComboBox class ignores wheel events."""
        cb = NoWheelComboBox()
        cb.addItem("A")
        cb.addItem("B")
        wheel_ev = QWheelEvent(
            QPoint(10, 10),
            QPoint(10, 10),
            QPoint(0, 120),
            QPoint(0, 120),
            Qt.NoButton,
            Qt.NoModifier,
            Qt.ScrollUpdate,
            False
        )
        cb.wheelEvent(wheel_ev)
        self.assertFalse(wheel_ev.isAccepted())
        cb.deleteLater()

    def test_determine_smart_defaults_pal(self):
        """Verifies PAL cadence detection when audio is 25 fps and video is 23.976 fps."""
        v_stream = make_metadata(
            id=0,
            codec="hevc",
            channels=0,
            sample_rate=0,
            fps=23.976,
            duration_ms=7200000.0,
            track_type="video",
            width=1920,
            height=1080
        )
        a_stream_pal = make_metadata(
            id=1,
            codec="ac3",
            channels=6,
            sample_rate=48000,
            fps=25.0,
            duration_ms=6912000.0,
            title="PAL Dub",
            language="por"
        )
        smart = determine_smart_defaults(v_stream, a_stream_pal)
        self.assertTrue(smart.pal_pitch_restore)
        self.assertIn("PAL", smart.pal_badge_text)
        self.assertEqual(smart.target_codec, "eac3")

    def test_determine_smart_defaults_lossless_codec(self):
        """Verifies lossless target codec selection when input is TrueHD / DTS-HD MA / FLAC."""
        v_stream = make_metadata(
            id=0,
            codec="h264",
            channels=0,
            sample_rate=0,
            fps=24.0,
            duration_ms=60000.0,
            track_type="video"
        )
        a_stream_flac = make_metadata(
            id=1,
            codec="flac",
            channels=6,
            sample_rate=48000,
            fps=24.0,
            duration_ms=60000.0,
            language="por"
        )
        smart = determine_smart_defaults(v_stream, a_stream_flac)
        self.assertFalse(smart.pal_pitch_restore)
        self.assertEqual(smart.target_codec, "flac")

    def test_determine_smart_defaults_stereo_lossy(self):
        """Verifies AAC/Opus target codec selection for stereo lossy audio."""
        v_stream = make_metadata(
            id=0,
            codec="h264",
            channels=0,
            sample_rate=0,
            fps=24.0,
            duration_ms=60000.0,
            track_type="video"
        )
        a_stream_stereo = make_metadata(
            id=1,
            codec="aac",
            channels=2,
            sample_rate=44100,
            fps=24.0,
            duration_ms=60000.0,
            language="por"
        )
        smart = determine_smart_defaults(v_stream, a_stream_stereo)
        self.assertFalse(smart.pal_pitch_restore)
        self.assertIn(smart.target_codec, ("aac", "opus"))

    def test_reset_to_recommended_state(self):
        """Verifies reset_to_recommended_state restores initial verdict selection."""
        dz = StreamReviewGate()
        try:
            v_cand = StreamCandidate(
                stream=make_metadata(id=0, codec="hevc", channels=0, sample_rate=0, fps=24.0, duration_ms=60000.0, track_type="video"),
                file_path="/tmp/video.mkv",
                is_recommended=True
            )
            a_target = StreamCandidate(
                stream=make_metadata(id=1, codec="ac3", channels=6, sample_rate=48000, fps=24.0, duration_ms=60000.0, language="por"),
                file_path="/tmp/dub.mkv",
                is_recommended=True
            )
            a_ref = StreamCandidate(
                stream=make_metadata(id=2, codec="dts", channels=6, sample_rate=48000, fps=24.0, duration_ms=60000.0, language="eng"),
                file_path="/tmp/video.mkv",
                is_recommended=True
            )
            verdict = AutoMatchVerdict(
                recommended_video=v_cand,
                recommended_target_audio=a_target,
                reference_audio=a_ref
            )
            dz.set_verdict(verdict)

            # Manually perturb state
            dz.check_pal_pitch.setChecked(True)
            dz.check_keep_original.setChecked(False)

            # Restore
            dz.reset_to_recommended_state()
            self.assertTrue(dz.check_keep_original.isChecked())
            self.assertFalse(dz.check_pal_pitch.isChecked())
            state = dz.get_review_state()
            self.assertEqual(state.selected_video_id, 0)
            self.assertEqual(state.selected_target_audio_id, 1)
            self.assertEqual(state.selected_ref_audio_id, 2)
            self.assertFalse(state.is_customized)
        finally:
            dz.deleteLater()

    def test_worker_preview_and_remux_signals(self):
        """Verifies worker signals preview_segments_ready, remux_progress, and remux_completed exist."""
        job = RemuxJob(
            output_path="/tmp/out.mkv",
            video_file="/tmp/v.mkv",
            target_audio_file="/tmp/a.mkv",
            offset_ms=0.0,
            stretch_ratio=1.0,
            keep_original_audio=True
        )
        worker = UnifiedPipelineWorker(job)
        self.assertTrue(hasattr(worker, "preview_segments_ready"))
        self.assertTrue(hasattr(worker, "remux_progress"))
        self.assertTrue(hasattr(worker, "remux_completed"))


if __name__ == "__main__":
    unittest.main()
