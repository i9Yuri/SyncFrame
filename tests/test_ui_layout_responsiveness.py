"""Unit tests for UI layout responsiveness, QScrollArea wrapping, theme switching, and header cleanup."""

import sys
import unittest
from unittest.mock import patch
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QScrollArea, QPushButton, QLabel

from src.core.models import StreamMetadata, StreamCandidate
from src.ui.main_window import SyncFrameMainWindow

# Ensure QApplication instance exists for offscreen Qt tests
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)


class TestUILayoutResponsiveness(unittest.TestCase):

    def setUp(self):
        self.window = SyncFrameMainWindow()

    def tearDown(self):
        self.window.deleteLater()

    def test_scroll_area_configured_properly(self):
        """Window hierarchy must wrap central cards in a QScrollArea with widgetResizable=True."""
        scroll_area = getattr(self.window, "scroll_area", None)
        self.assertIsNotNone(scroll_area, "MainWindow must have a scroll_area attribute")
        self.assertIsInstance(scroll_area, QScrollArea)
        self.assertTrue(scroll_area.widgetResizable())
        self.assertIsNotNone(scroll_area.widget(), "Scroll area must contain a body container widget")

    def test_header_sanitization(self):
        """Header must NOT contain 'Anti-Slop Engine' text or badges."""
        labels = self.window.findChildren(QLabel)
        for lbl in labels:
            text = lbl.text()
            self.assertNotIn("Anti-Slop Engine", text, f"Label contains forbidden text: {text}")

    def test_theme_switcher(self):
        """Theme toggle must switch between dark and light themes dynamically."""
        self.assertEqual(self.window.current_theme, "dark")
        self.assertIn("Modo Claro", self.window.btn_theme.toolTip())
        self.assertFalse(self.window.btn_theme.icon().isNull())

        # Toggle to light theme
        self.window.btn_theme.click()
        self.assertEqual(self.window.current_theme, "light")
        self.assertIn("Modo Escuro", self.window.btn_theme.toolTip())
        self.assertFalse(self.window.btn_theme.icon().isNull())

        # Toggle back to dark theme
        self.window.btn_theme.click()
        self.assertEqual(self.window.current_theme, "dark")
        self.assertIn("Modo Claro", self.window.btn_theme.toolTip())
        self.assertFalse(self.window.btn_theme.icon().isNull())

    def test_windowed_mode_resizing(self):
        """Verifies that window resizes gracefully without overlapping or raising layout errors."""
        resolutions = [
            (1280, 800),
            (1024, 650),
            (900, 550),
            (800, 540)  # Minimum window size
        ]

        for width, height in resolutions:
            self.window.resize(width, height)
            self.window.updateGeometry()
            # Force layout recalculation
            self.window.layout().activate()

            # Ensure current dimensions match or exceed minimum constraints
            self.assertGreaterEqual(self.window.width(), 800)
            self.assertGreaterEqual(self.window.height(), 540)

            # Ensure body container exists and scroll area is responsive
            container = self.window.scroll_area.widget()
            self.assertIsNotNone(container)
            self.assertGreater(container.layout().count(), 0)

    def test_confirmation_and_reset_flow(self):
        """Tests confirmation propagation and clean reset."""
        v_stream = StreamMetadata(
            id=0, codec="HEVC", channels=0, sample_rate=0, fps=23.976,
            duration_ms=5000000.0, language="und", is_default=True,
            track_type="video", width=3840, height=2160, bitrate=20_000_000
        )
        cand_v = StreamCandidate(file_path="/tmp/test_vid.mkv", stream=v_stream, score=100.0)

        a_stream = StreamMetadata(
            id=2, codec="AAC", channels=2, sample_rate=48000, fps=0.0,
            duration_ms=5000000.0, language="por", is_default=True,
            track_type="audio", title="Dublado"
        )
        cand_a = StreamCandidate(file_path="/tmp/test_aud.mkv", stream=a_stream, score=90.0)

        # Trigger confirmation handler with mocked start_analysis
        with patch.object(self.window, "start_analysis") as mock_start:
            self.window._on_confirmation_confirmed(cand_v, cand_a, None, True)
            mock_start.assert_called_once()
            self.assertTrue(self.window.auto_chain_remux)

        self.assertEqual(self.window.video_path, "/tmp/test_vid.mkv")
        self.assertEqual(self.window.audio_path, "/tmp/test_aud.mkv")
        self.assertEqual(self.window.selected_video_track_id, 0)
        self.assertEqual(self.window.selected_target_audio_id, 2)
        self.assertTrue(self.window.check_keep_original.isChecked())
        self.assertTrue(self.window.txt_output_path.text().endswith("test_vid_synced.mkv"))

        # Trigger reset
        self.window._on_reset_requested()
        self.assertIsNone(self.window.video_path)
        self.assertIsNone(self.window.audio_path)
        self.assertEqual(self.window.txt_output_path.text(), "")

    def test_sticky_detached_topbar_structure(self):
        """Top bar must be detached from scroll area with fixed 76px height and distinct theme styling."""
        topbar = getattr(self.window, "topbar", None)
        self.assertIsNotNone(topbar)
        self.assertEqual(topbar.objectName(), "topHeader")
        self.assertEqual(topbar.height(), 76)

        # Ensure scroll area is positioned below the sticky topbar
        self.window.resize(1024, 720)
        self.window.show()
        QApplication.processEvents()

        self.assertGreaterEqual(self.window.scroll_area.y(), 76)

        # Validate dark theme topbar styling
        img_dark = topbar.grab().toImage()
        self.assertEqual(img_dark.pixelColor(10, 10).name(), "#121316")
        self.assertEqual(img_dark.pixelColor(10, 75).name(), "#23252b")

        # Toggle to light theme and validate styling
        self.window.toggle_theme_mode()
        QApplication.processEvents()
        img_light = topbar.grab().toImage()
        self.assertEqual(img_light.pixelColor(10, 10).name(), "#ffffff")
        self.assertEqual(img_light.pixelColor(10, 75).name(), "#e1e4ed")


if __name__ == "__main__":
    unittest.main()
