"""Unit tests for UI ingestion state transitions, review gate activation, and theme contrast."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

from PySide6.QtWidgets import QApplication, QBoxLayout

from src.core.models import (
    StreamMetadata,
    StreamCandidate,
    AutoMatchVerdict,
    MediaSourceInfo
)
from src.ui.main_window import SyncFrameMainWindow
from src.ui.style import get_theme_stylesheet, get_theme_tokens, apply_one_ui_monochrome_theme

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

    def test_elide_filename_middle_truncation(self):
        """Verifies middle elision preserves stem prefix, suffix, and extension while keeping length constrained."""
        from src.ui.components.unified_drop_zone import elide_filename

        short_name = "sample.mkv"
        self.assertEqual(elide_filename(short_name, max_chars=36), short_name)

        long_name = "The.Avengers.Endgame.2019.2160p.UHD.Remux.HEVC.DTS-HD.MA.7.1-DTOne.mkv"
        elided = elide_filename(long_name, max_chars=36)
        self.assertLessEqual(len(elided), 36)
        self.assertIn("...", elided)
        self.assertTrue(elided.endswith(".mkv"))
        self.assertTrue(elided.startswith("The."))

    def test_configure_stream_row_contract(self):
        """Verifies configure_stream_row builds a two-level card conforming to the layout contract."""
        from PySide6.QtWidgets import QComboBox
        drop_zone = self.window.drop_zone

        # Test 4-argument call (without combo: uses description label)
        row_desc = drop_zone.configure_stream_row(
            track_id="A03 / Secundário",
            role_badge="Opcional",
            description="Codec AAC 2.0 • 192 kbps",
            action_chip="Copy",
            combo=None
        )
        self.assertEqual(row_desc.lbl_id.text(), "A03 / Secundário")
        self.assertEqual(row_desc.badge.text(), "Opcional")
        self.assertEqual(row_desc.chip.text(), "Copy")
        self.assertEqual(row_desc.lbl_desc.text(), "Codec AAC 2.0 • 192 kbps")
        self.assertGreaterEqual(row_desc.chip.minimumWidth(), 64)

        # Test 5-argument call with QComboBox (embedded in lower line)
        combo = QComboBox()
        row_combo = drop_zone.configure_stream_row(
            track_id="V01 / Vídeo",
            role_badge="Melhor Imagem",
            description="",
            action_chip="Copy",
            combo=combo
        )
        self.assertEqual(row_combo.lbl_id.text(), "V01 / Vídeo")
        self.assertEqual(row_combo.badge.text(), "Melhor Imagem")
        self.assertEqual(row_combo.chip.text(), "Copy")
        self.assertIs(row_combo.combo, combo)
        self.assertGreaterEqual(row_combo.chip.minimumWidth(), 64)

    def test_role_badge_dynamic_autofit_no_truncation(self):
        """Verifies update_role_badge computes dynamic width preventing clipping of long labels."""
        drop_zone = self.window.drop_zone
        badge = drop_zone.badge_v_status

        test_labels = [
            "Melhor Imagem",
            "Português Oficial",
            "Referência Fixa",
            "Ajuste Manual"
        ]
        for label in test_labels:
            drop_zone.update_role_badge(badge, label)
            self.assertEqual(badge.text(), label)
            expected_min = max(badge.fontMetrics().horizontalAdvance(label) + 24, 88)
            self.assertGreaterEqual(badge.minimumWidth(), expected_min)

    def test_autonomous_left_column_blocks(self):
        """Verifies the left column is decomposed into 3 autonomous visual containers."""
        drop_zone = self.window.drop_zone
        self.assertTrue(hasattr(drop_zone, "block_sources"))
        self.assertTrue(hasattr(drop_zone, "frame_arbitration"))
        self.assertTrue(hasattr(drop_zone, "block_review"))

        self.assertEqual(drop_zone.block_sources.property("class"), "subCard")
        self.assertEqual(drop_zone.frame_arbitration.property("class"), "arbitrationCard")
        self.assertEqual(drop_zone.block_review.property("class"), "subCard")

    def test_role_badge_and_action_chip_styles(self):
        """Verifies get_role_badge_style and get_action_chip_style produce valid non-empty QSS."""
        drop_zone = self.window.drop_zone

        badge_style_img = drop_zone.get_role_badge_style("Melhor Imagem")
        badge_style_pt = drop_zone.get_role_badge_style("Português")
        self.assertIn("border-radius", badge_style_img)
        self.assertIn("border-radius", badge_style_pt)

        chip_style_copy = drop_zone.get_action_chip_style("Copy")
        chip_style_align = drop_zone.get_action_chip_style("Align")
        self.assertIn("min-width", chip_style_copy)
        self.assertIn("min-width", chip_style_align)

    def test_one_ui_monochrome_tokens(self):
        """Verifies get_theme_tokens returns exact required monochrome color palette tokens."""
        dark_tokens = get_theme_tokens("dark")
        self.assertEqual(dark_tokens["bg_base"], "#000000")
        self.assertEqual(dark_tokens["bg_card"], "#1b1c20")
        self.assertEqual(dark_tokens["text_primary"], "#f2f3f7")
        self.assertEqual(dark_tokens["border_subtle"], "#2d2f36")

        light_tokens = get_theme_tokens("light")
        self.assertEqual(light_tokens["bg_base"], "#f1f2f6")
        self.assertEqual(light_tokens["bg_card"], "#ffffff")
        self.assertEqual(light_tokens["text_primary"], "#16181d")
        self.assertEqual(light_tokens["border_subtle"], "#dcdfe8")

    def test_responsive_column_collapse(self):
        """Verifies responsive layout collapses to TopToBottom below 960px and LeftToRight at >=960px."""
        from PySide6.QtGui import QResizeEvent
        from PySide6.QtCore import QSize

        # Resize to 800px width (< 960px)
        self.window.resize(800, 600)
        self.window.resizeEvent(QResizeEvent(QSize(800, 600), self.window.size()))
        self.assertEqual(self.window.body_layout.direction(), QBoxLayout.TopToBottom)

        # Resize to 1280px width (>= 960px)
        self.window.resize(1280, 800)
        self.window.resizeEvent(QResizeEvent(QSize(1280, 800), self.window.size()))
        self.assertEqual(self.window.body_layout.direction(), QBoxLayout.LeftToRight)

    def test_floating_dock_and_pill_geometry(self):
        """Verifies floating bottom dock container presence and pill badge styling."""
        self.assertTrue(hasattr(self.window, "dock_container"))
        self.assertEqual(self.window.log_drawer.property("class"), "floatingDock")
        self.assertEqual(self.window.log_drawer.objectName(), "floatingDock")

        # Verify QSS contains 28px card radius and 999px pill radii
        dark_qss = get_theme_stylesheet("dark")
        self.assertIn("border-radius: 28px", dark_qss)
        self.assertIn("border-radius: 34px", dark_qss)
        self.assertIn("border-radius: 999px", dark_qss)


if __name__ == "__main__":
    unittest.main()


