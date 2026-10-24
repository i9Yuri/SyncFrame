"""End-to-end integration test consuming real Avengers files in read-only mode."""

import os
import sys
import unittest
from unittest.mock import patch

from PySide6.QtCore import QEventLoop, QTimer, Qt
from PySide6.QtWidgets import QApplication

from src.core.inspector import inspect_media, evaluate_media_streams
from src.ui.main_window import SyncFrameMainWindow

app = QApplication.instance() or QApplication([])

REF_4K = "/home/yuri/Downloads/Torrent downloads/The.Avengers.2012.Multi.Bluray.2160p.x265.HDR.Atmos.7.1-DTOne.mkv"
TARGET_1080P = "/home/yuri/Downloads/Torrent downloads/Os.Vingadores.2012.1080p-WOLVERDONFILMES.COM.mkv"
OUT_TEMP = "/home/yuri/Downloads/Torrent downloads/test_avengers_synced_pipeline.mkv"


class TestLiveAvengersPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.isfile(REF_4K) or not os.path.isfile(TARGET_1080P):
            raise unittest.SkipTest("Real Avengers test files not available in ~/Downloads/Torrent downloads/")

    def setUp(self):
        self.window = SyncFrameMainWindow()

    def tearDown(self):
        if hasattr(self.window, "active_worker") and self.window.active_worker and self.window.active_worker.isRunning():
            self.window.active_worker.cancel()
            self.window.active_worker.wait(3000)
        self.window.close()
        if os.path.isfile(OUT_TEMP):
            try:
                os.remove(OUT_TEMP)
            except Exception:
                pass

    @patch("src.ui.main_window.check_disk_space", return_value=(True, 200 * 1024**3, 10 * 1024**3))
    def test_live_avengers_end_to_end_correlation_flow(self, mock_disk):
        """
        Validates real end-to-end acoustic pipeline against Avengers test media:
        - Auto-matches 4K reference video & 1080p dubbing
        - Extracts 16kHz PCM samples
        - Computes FFT cross-correlation
        - Populates correlation curve and offset (-829 ms)
        - Updates confidence and drift
        - Enables lip-sync markers
        """
        verdict = evaluate_media_streams(REF_4K, TARGET_1080P)

        self.assertIsNotNone(verdict)
        self.assertEqual(verdict.recommended_video.file_path, REF_4K)
        self.assertEqual(verdict.recommended_target_audio.file_path, TARGET_1080P)

        # Set up destination path
        self.window.txt_output_path.setText(OUT_TEMP)

        # Ingest verdict into dropzone
        self.window.drop_zone.set_verdict(verdict)

        # Wait for correlation to complete using QEventLoop
        loop = QEventLoop()
        correlation_done = [False]
        detected_offset = [0.0]

        def _on_offset(offset_ms: float):
            if abs(offset_ms) > 10.0:
                correlation_done[0] = True
                detected_offset[0] = offset_ms
                # Cancel remux step immediately to save disk I/O and verify correlation metrics
                if hasattr(self.window, "active_worker") and self.window.active_worker:
                    self.window.active_worker.cancel()
                loop.quit()

        self.window.sync_controls.offset_changed.connect(_on_offset)

        # Confirm selection in Review Gate
        self.window.drop_zone.btn_confirm.click()

        if hasattr(self.window, "active_worker") and self.window.active_worker:
            def _on_fail(err):
                loop.quit()
            self.window.active_worker.execution_failed.connect(_on_fail)

        # Safety timeout after 45 seconds (sample extraction + FFT takes ~6s)
        QTimer.singleShot(45000, loop.quit)
        loop.exec()

        self.assertTrue(correlation_done[0], "Acoustic correlation did not complete within timeout.")
        self.assertAlmostEqual(detected_offset[0], -829.0, delta=20.0)

        # Verify UI state reflects the calculated correlation
        self.assertIn("829", self.window.sync_controls.lbl_offset_val.text())
        self.assertNotEqual(self.window.sync_controls.lbl_confidence.text(), "Não analisado")
        self.assertTrue(len(self.window.correlation_view._curve_data) > 0)
        self.assertTrue(self.window.preview_player.btn_m5.isEnabled())
        self.assertTrue(self.window.preview_player.btn_m50.isEnabled())
        self.assertTrue(self.window.preview_player.btn_m90.isEnabled())
        self.assertGreater(self.window.log_drawer.event_count, 0)


if __name__ == "__main__":
    unittest.main()
