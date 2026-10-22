"""Unit tests for SyncFrame data contracts and models."""

import unittest
from src.core.models import StreamMetadata, InspectionResult, SyncMetrics, RemuxJob


class TestModels(unittest.TestCase):

    def test_stream_metadata_label(self):
        video_stream = StreamMetadata(
            id=0,
            codec="AVC/H.264",
            channels=0,
            sample_rate=0,
            fps=23.976023,
            duration_ms=7200000.0,
            language="eng",
            is_default=True,
            track_type="video",
            width=1920,
            height=1080
        )
        label = video_stream.display_label()
        self.assertIn("Vídeo #0", label)
        self.assertIn("1920x1080", label)
        self.assertIn("23.976 fps", label)
        self.assertIn("[Padrão]", label)

        audio_stream = StreamMetadata(
            id=1,
            codec="E-AC-3",
            channels=6,
            sample_rate=48000,
            fps=0.0,
            duration_ms=7200000.0,
            language="por",
            is_default=True,
            track_type="audio",
            title="Dublagem Clássica"
        )
        audio_label = audio_stream.display_label()
        self.assertIn("Áudio #1 (POR)", audio_label)
        self.assertIn("6ch", audio_label)
        self.assertIn("48000Hz", audio_label)
        self.assertIn("Dublagem Clássica", audio_label)

    def test_sync_metrics_confidence(self):
        m_high = SyncMetrics(
            static_offset_ms=350.0,
            drift_ratio=1.0,
            confidence_score=0.88,
            detected_fps_mismatch=False
        )
        self.assertTrue(m_high.is_confident)

        m_low = SyncMetrics(
            static_offset_ms=10.0,
            drift_ratio=1.0,
            confidence_score=0.20,
            detected_fps_mismatch=False
        )
        self.assertFalse(m_low.is_confident)

    def test_remux_job_instantiation(self):
        job = RemuxJob(
            output_path="/tmp/output.mkv",
            video_file="/tmp/video.mkv",
            target_audio_file="/tmp/audio.mkv",
            offset_ms=-250.0,
            stretch_ratio=1.0,
            keep_original_audio=True
        )
        self.assertEqual(job.offset_ms, -250.0)
        self.assertTrue(job.keep_original_audio)
        self.assertEqual(job.target_audio_language, "por")


if __name__ == "__main__":
    unittest.main()
