"""Unit tests for PipelineWorker contract signals, audiophile recommendation badges, and control styling."""

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtWidgets import QApplication

from src.core.models import (
    RemuxJob,
    StreamMetadata,
    SyncMetrics,
)
from src.core.inspector import (
    format_audiophile_recommendation_badge,
    format_audiophile_discard_notice,
)
from src.ui.workers import PipelineWorker, UnifiedPipelineWorker
from src.ui.style import (
    get_check_icon_path,
    get_theme_stylesheet,
    get_role_badge_style,
    DARK_THEME_QSS,
    LIGHT_THEME_QSS,
)
from src.ui.components.unified_drop_zone import UnifiedDropZone
from src.ui.components.sync_controls import SyncControls

app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)


class TestPipelineSignalsAndStyles(unittest.TestCase):
    """Validates worker contract signals, recommendation badges, and rounded container styles."""

    def test_pipeline_worker_alias(self):
        """Ensures PipelineWorker is an alias of UnifiedPipelineWorker."""
        self.assertIs(PipelineWorker, UnifiedPipelineWorker)

    def test_audiophile_recommendation_badges(self):
        """Validates didactic recommendation badges across lossless, surround, and lossy streams."""
        # Lossless stream
        s_dts = StreamMetadata(
            id=1,
            track_type="audio",
            codec="dts",
            channels=6,
            sample_rate=48000,
            fps=0.0,
            duration_ms=60000.0,
            is_default=True,
            bitrate=1500000,
            title="DTS-HD MA 5.1 Lossless",
            language="por"
        )
        badge_dts, desc_dts = format_audiophile_recommendation_badge(s_dts)
        self.assertEqual(badge_dts, "ÁUDIO DE MAIOR FIDELIDADE")
        self.assertIn("Fidelidade Máxima (Lossless", desc_dts)

        # Immersive / Surround AC3 stream
        s_ac3 = StreamMetadata(
            id=2,
            track_type="audio",
            codec="eac3",
            channels=6,
            sample_rate=48000,
            fps=0.0,
            duration_ms=60000.0,
            is_default=False,
            bitrate=640000,
            is_immersive=True,
            spatial_label="Dolby Atmos",
            language="por"
        )
        badge_ac3, desc_ac3 = format_audiophile_recommendation_badge(s_ac3)
        self.assertIn("RECOMENDADA", badge_ac3)
        self.assertIn("Dolby Atmos", desc_ac3)

        # Standard lossy AAC stereo
        s_aac = StreamMetadata(
            id=3,
            track_type="audio",
            codec="aac",
            channels=2,
            sample_rate=44100,
            fps=0.0,
            duration_ms=60000.0,
            is_default=False,
            bitrate=128000,
            language="por"
        )
        badge_aac, desc_aac = format_audiophile_recommendation_badge(s_aac)
        self.assertIn("OFICIAL", badge_aac)
        self.assertIn("AAC", desc_aac)

    def test_audiophile_discard_notice(self):
        """Validates that discard explanation correctly warns against lower-tier discarded streams."""
        s_low = StreamMetadata(
            id=2,
            track_type="audio",
            codec="aac",
            channels=2,
            sample_rate=44100,
            fps=0.0,
            duration_ms=60000.0,
            is_default=False,
            bitrate=128000,
            language="por"
        )
        notice = format_audiophile_discard_notice(s_low)
        self.assertIn("Descartada", notice)
        self.assertIn("AAC", notice)

    def test_role_badge_style_handles_recommendation(self):
        """Ensures get_role_badge_style applies styling to recommendation badges."""
        style_rec = get_role_badge_style("ÁUDIO DE MAIOR FIDELIDADE")
        self.assertIn("border-radius", style_rec)

        style_rec2 = get_role_badge_style("[MELHOR OPÇÃO RECOMENDADA]")
        self.assertIn("border-radius", style_rec2)

    def test_check_glyph_exists_and_styled(self):
        """Verifies the check glyph icon path and its presence in Dark and Light stylesheets."""
        path = get_check_icon_path()
        self.assertTrue(os.path.isfile(path), f"Check glyph does not exist at {path}")
        self.assertGreater(os.path.getsize(path), 0)

        dark_qss = get_theme_stylesheet("dark")
        light_qss = get_theme_stylesheet("light")

        self.assertIn(path, dark_qss)
        self.assertIn(path, light_qss)

    def test_container_and_badge_styles_in_stylesheets(self):
        """Verifies optionsContainer, sliderContainer, and badgeRecommended exist in themes."""
        for mode in ("dark", "light"):
            qss = get_theme_stylesheet(mode)
            self.assertIn("optionsContainer", qss)
            self.assertIn("sliderContainer", qss)
            self.assertIn("badgeRecommended", qss)

    def test_drop_zone_options_container_frame(self):
        """Verifies UnifiedDropZone wraps options row inside optionsContainer frame."""
        dz = UnifiedDropZone()
        try:
            self.assertTrue(hasattr(dz, "frame_options"))
            self.assertEqual(dz.frame_options.property("class"), "optionsContainer")
            self.assertEqual(dz.frame_options.objectName(), "frameOptions")
        finally:
            dz.deleteLater()

    def test_sync_controls_slider_container_frame(self):
        """Verifies SyncControls wraps slider inside sliderContainer frame."""
        sc = SyncControls()
        try:
            self.assertTrue(hasattr(sc, "frame_slider"))
            self.assertEqual(sc.frame_slider.property("class"), "sliderContainer")
            self.assertEqual(sc.frame_slider.objectName(), "frameSlider")
        finally:
            sc.deleteLater()

    def test_worker_signals_contract(self):
        """Verifies UnifiedPipelineWorker declares all required signals and parent support."""
        job = RemuxJob(
            output_path="/tmp/test_out.mkv",
            video_file="/tmp/v.mkv",
            target_audio_file="/tmp/a.mkv",
            offset_ms=0.0,
            stretch_ratio=1.0,
            keep_original_audio=True,
            target_track_id=1,
            target_audio_track_id=1,
            ref_audio_track_id=1
        )
        worker = UnifiedPipelineWorker(job, manual_offset_override=120.0, parent=None)
        self.assertTrue(hasattr(worker, "analysis_started"))
        self.assertTrue(hasattr(worker, "step_progress"))
        self.assertTrue(hasattr(worker, "correlation_ready"))
        self.assertTrue(hasattr(worker, "correlation_completed"))
        self.assertTrue(hasattr(worker, "preview_ready"))
        self.assertTrue(hasattr(worker, "finished_success"))
        self.assertTrue(hasattr(worker, "execution_failed"))
        self.assertTrue(hasattr(worker, "metrics_ready"))
        self.assertTrue(hasattr(worker, "completed"))
        self.assertTrue(hasattr(worker, "log_message"))

    def test_worker_cancellation_emits_failure(self):
        """Verifies worker immediately terminates and emits execution_failed when cancelled."""
        job = RemuxJob(
            output_path="/tmp/test_out.mkv",
            video_file="/tmp/v.mkv",
            target_audio_file="/tmp/a.mkv",
            offset_ms=0.0,
            stretch_ratio=1.0,
            keep_original_audio=True
        )
        worker = UnifiedPipelineWorker(job)
        worker.cancel()

        failed_signals = []
        completed_signals = []
        worker.execution_failed.connect(failed_signals.append)
        worker.completed.connect(lambda ok, msg: completed_signals.append((ok, msg)))

        worker.run()
        self.assertEqual(len(failed_signals), 1)
        self.assertIn("cancelada", failed_signals[0].lower())
        self.assertEqual(len(completed_signals), 1)
        self.assertFalse(completed_signals[0][0])


if __name__ == "__main__":
    unittest.main()
