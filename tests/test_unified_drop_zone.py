"""Unit tests for UnifiedDropZone component, multi-file ingestion, and confirmation table."""

import os
import sys
import unittest
from PySide6.QtWidgets import QApplication

from src.core.models import StreamMetadata, StreamCandidate, AutoMatchVerdict
from src.ui.components.unified_drop_zone import UnifiedDropZone

# Ensure QApplication instance exists for offscreen Qt tests
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)


class TestUnifiedDropZone(unittest.TestCase):

    def setUp(self):
        self.drop_zone = UnifiedDropZone()

    def tearDown(self):
        self.drop_zone.deleteLater()

    def test_initial_state(self):
        """Drop zone should begin at page 0 (empty standby)."""
        self.assertEqual(self.drop_zone.stack.currentIndex(), 0)
        self.assertEqual(len(self.drop_zone.loaded_files), 0)

    def test_single_file_ingestion(self):
        """Single file ingestion transitions to page 1 awaiting second file."""
        self.drop_zone.ingest_files(["/tmp/mock_video_a.mkv"])
        self.assertEqual(len(self.drop_zone.loaded_files), 1)
        self.assertEqual(self.drop_zone.stack.currentIndex(), 1)
        self.assertIn("mock_video_a.mkv", self.drop_zone.lbl_single_filename.text())

    def test_dual_file_ingestion_emits_signal(self):
        """Dual file ingestion emits files_ready with both files."""
        received_files = []

        def on_files_ready(f_a, f_b):
            received_files.extend([f_a, f_b])

        self.drop_zone.files_ready.connect(on_files_ready)
        self.drop_zone.ingest_files(["/tmp/mock_video_a.mkv", "/tmp/mock_audio_b.mkv"])

        self.assertEqual(len(received_files), 2)
        self.assertTrue(received_files[0].endswith("mock_video_a.mkv"))
        self.assertTrue(received_files[1].endswith("mock_audio_b.mkv"))

    def test_set_verdict_and_confirmation(self):
        """Populating verdict moves to Review Gate and confirmation emits verified streams."""
        v_stream = StreamMetadata(
            id=0, codec="HEVC", channels=0, sample_rate=0, fps=23.976,
            duration_ms=7200000.0, language="und", is_default=True,
            track_type="video", width=3840, height=2160, bitrate=25_000_000
        )
        cand_v = StreamCandidate(file_path="/tmp/video_4k.mkv", stream=v_stream, score=100.0)

        a_stream = StreamMetadata(
            id=1, codec="AC-3", channels=6, sample_rate=48000, fps=0.0,
            duration_ms=7200000.0, language="por", is_default=True,
            track_type="audio", title="Dublagem Brasileira"
        )
        cand_a = StreamCandidate(file_path="/tmp/audio_dub.mkv", stream=a_stream, score=90.0)

        ref_stream = StreamMetadata(
            id=1, codec="DTS-HD", channels=8, sample_rate=48000, fps=0.0,
            duration_ms=7200000.0, language="eng", is_default=True,
            track_type="audio", title="English Original"
        )
        cand_ref = StreamCandidate(file_path="/tmp/video_4k.mkv", stream=ref_stream, score=80.0)

        verdict = AutoMatchVerdict(
            recommended_video=cand_v,
            recommended_target_audio=cand_a,
            reference_audio=cand_ref,
            alternative_videos=[],
            alternative_audios=[cand_ref]
        )

        self.drop_zone.set_verdict(verdict)
        self.assertEqual(self.drop_zone.stack.currentIndex(), 2)

        confirmed_data = []

        def on_confirmed(v, target, ref, keep_orig):
            confirmed_data.append((v, target, ref, keep_orig))

        self.drop_zone.confirmation_confirmed.connect(on_confirmed)
        self.drop_zone.btn_confirm.click()

        self.assertEqual(len(confirmed_data), 1)
        chosen_v, chosen_target, chosen_ref, keep_orig = confirmed_data[0]
        self.assertEqual(chosen_v.file_path, "/tmp/video_4k.mkv")
        self.assertEqual(chosen_target.file_path, "/tmp/audio_dub.mkv")
        self.assertEqual(chosen_ref.file_path, "/tmp/video_4k.mkv")
        self.assertTrue(keep_orig)

    def test_reset(self):
        """Reset clears loaded files and resets stack back to standby page 0."""
        self.drop_zone.ingest_files(["/tmp/mock_a.mkv"])
        self.assertEqual(self.drop_zone.stack.currentIndex(), 1)

        reset_emitted = []
        self.drop_zone.reset_requested.connect(lambda: reset_emitted.append(True))

        self.drop_zone.reset()
        self.assertEqual(self.drop_zone.stack.currentIndex(), 0)
        self.assertEqual(len(self.drop_zone.loaded_files), 0)
        self.assertEqual(len(reset_emitted), 1)


if __name__ == "__main__":
    unittest.main()
