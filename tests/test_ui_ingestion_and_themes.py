"""Unit tests for UI ingestion state transitions, review gate activation, and theme contrast."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

from PySide6.QtWidgets import QApplication

from src.core.models import (
    StreamMetadata,
    StreamCandidate,
    AutoMatchVerdict,
    MediaSourceInfo
)
from src.ui.main_window import SyncFrameMainWindow
from src.ui.style import get_theme_stylesheet

app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)


class TestUIIngestionAndThemes(unittest.TestCase):

    def setUp(self):
        self.window = SyncFrameMainWindow()

    def tearDown(self):
        self.window.deleteLater()

    def test_single_file_ingestion_transitions_to_page_1(self):
        """Single file ingestion transitions the drop zone to Page 1 awaiting the second file."""
        self.assertEqual(self.window.drop_zone.stack.currentIndex(), 0)
        self.window.handle_files_ingested(["/tmp/mock_sample_video.mkv"])
        self.assertEqual(self.window.drop_zone.stack.currentIndex(), 1)
        self.assertEqual(len(self.window.drop_zone.loaded_files), 1)
        self.assertIn("mock_sample_video.mkv", self.window.drop_zone.lbl_single_filename.text())

    @patch("src.ui.main_window.evaluate_media_streams")
    def test_dual_file_ingestion_transitions_to_page_2_review_gate(self, mock_evaluate):
        """Dual file ingestion triggers auto-matching and transitions drop zone to Page 2 (Review Gate)."""
        v_stream = StreamMetadata(
            id=0, codec="HEVC", channels=0, sample_rate=0, fps=23.976,
            duration_ms=5000000.0, language="und", is_default=True,
            track_type="video", width=3840, height=2160, bitrate=25_000_000
        )
        cand_v = StreamCandidate(file_path="/tmp/video_main.mkv", stream=v_stream, score=100.0)

        a_stream = StreamMetadata(
            id=1, codec="AC-3", channels=6, sample_rate=48000, fps=0.0,
            duration_ms=5000000.0, language="por", is_default=True,
            track_type="audio", channel_layout="5.1(side)"
        )
        cand_a = StreamCandidate(file_path="/tmp/audio_dub.mkv", stream=a_stream, score=90.0)

        verdict = AutoMatchVerdict(
            recommended_video=cand_v,
            recommended_target_audio=cand_a,
            reference_audio=None,
            alternative_videos=[],
            alternative_audios=[]
        )
        mock_evaluate.return_value = verdict

        self.window.handle_files_ingested(["/tmp/video_main.mkv", "/tmp/audio_dub.mkv"])

        # Page 2 corresponds to Review Gate
        self.assertEqual(self.window.drop_zone.stack.currentIndex(), 2)
        mock_evaluate.assert_called_once_with("/tmp/video_main.mkv", "/tmp/audio_dub.mkv")
        self.assertIn("video_main.mkv", self.window.drop_zone.lbl_v_filename.text())
        self.assertIn("audio_dub.mkv", self.window.drop_zone.lbl_a_filename.text())
        self.assertIn("video_main.SYNCED.mkv", self.window.txt_output_path.text())

    def test_update_sources_view_explicit_contracts(self):
        """Verifies update_sources_view correctly populates UI card labels with MediaSourceInfo."""
        sources = [
            MediaSourceInfo(
                file_path="/tmp/my_feature_film.mkv",
                file_size_formatted="8.4 GB",
                extension="MKV",
                role_label="Fonte de Vídeo Principal",
                summary="3840x2160 • HEVC • 23.976 fps",
                is_video_source=True
            ),
            MediaSourceInfo(
                file_path="/tmp/my_dubbed_audio.mp4",
                file_size_formatted="450 MB",
                extension="MP4",
                role_label="Fonte de Áudio Dublado",
                summary="POR • AC-3 • 5.1 Surround",
                is_video_source=False
            )
        ]

        self.window.update_sources_view(sources)

        self.assertEqual(self.window.drop_zone.stack.currentIndex(), 2)
        self.assertEqual(self.window.drop_zone.lbl_v_filename.text(), "my_feature_film.mkv")
        self.assertEqual(self.window.drop_zone.lbl_v_meta.text(), "3840x2160 • HEVC • 23.976 fps")
        self.assertEqual(self.window.drop_zone.badge_v_fmt.text(), "MKV")

        self.assertEqual(self.window.drop_zone.lbl_a_filename.text(), "my_dubbed_audio.mp4")
        self.assertEqual(self.window.drop_zone.lbl_a_meta.text(), "POR • AC-3 • 5.1 Surround")
        self.assertEqual(self.window.drop_zone.badge_a_fmt.text(), "MP4")

    def test_apply_application_theme_atomic_and_contrast(self):
        """Verifies apply_application_theme switches QSS and removes inline color collisions."""
        # Test dark theme
        self.window.apply_application_theme("dark")
        self.assertEqual(self.window.current_theme, "dark")
        self.assertEqual(self.window.btn_theme.text(), "Modo Claro")

        dark_qss = get_theme_stylesheet("dark")
        self.assertIn("#0a0b0d", dark_qss)
        self.assertIn("#eef0f2", dark_qss)
        self.assertIn("#111317", dark_qss)

        # Test light theme
        self.window.apply_application_theme("light")
        self.assertEqual(self.window.current_theme, "light")
        self.assertEqual(self.window.btn_theme.text(), "Modo Escuro")

        light_qss = get_theme_stylesheet("light")
        self.assertIn("#f2f3f1", light_qss)
        self.assertIn("#191c1a", light_qss)
        self.assertIn("#ffffff", light_qss)

        # Ensure no saturated colors in stylesheets (strict monochrome)
        for qss, mode in [(dark_qss, "dark"), (light_qss, "light")]:
            self.assertNotIn("#10b981", qss)  # emerald green
            self.assertNotIn("#059669", qss)
            self.assertNotIn("#22c55e", qss)
            self.assertNotIn("#3b82f6", qss)  # blue
            self.assertNotIn("#06b6d4", qss)  # cyan
            self.assertNotIn("#f59e0b", qss)  # amber
            self.assertNotIn("#84cc16", qss)  # lime

    def test_log_drawer_contrast_in_light_and_dark_mode(self):
        """Verifies log drawer title has no hardcoded dark inline style causing black-on-dark or white-on-light."""
        title_lbl = self.window.log_drawer.title_lbl
        self.assertEqual(title_lbl.property("class"), "logTitle")
        self.assertEqual(title_lbl.styleSheet(), "")


if __name__ == "__main__":
    unittest.main()
