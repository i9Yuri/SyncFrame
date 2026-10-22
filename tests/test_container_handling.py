"""Unit and integration tests for multi-container media probing, audio profiles, demuxing, and hybrid remux."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from PySide6.QtWidgets import QApplication

from src.core.extractor import extract_audio_lossless
from src.core.inspector import probe_media_file, inspect_media
from src.core.models import (
    AudioProfile,
    AutoMatchVerdict,
    StreamCandidate,
    StreamMetadata,
    format_channel_layout_label
)
from src.core.remuxer import build_mkvmerge_hybrid_command
from src.ui.components.unified_drop_zone import UnifiedDropZone

# Ensure QApplication instance for UI tests
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)


class TestContainerHandling(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="syncframe_test_container_")
        cls.mp4_stereo = os.path.join(cls.temp_dir, "test_stereo.mp4")
        cls.mp4_surround = os.path.join(cls.temp_dir, "test_surround.mp4")
        cls.mkv_source = os.path.join(cls.temp_dir, "test_source.mkv")

        # 1. Generate synthetic MP4 with H.264 video and AAC Stereo audio
        cmd_stereo = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=24",
            "-f", "lavfi", "-i", "sine=frequency=1000:duration=1:sample_rate=48000",
            "-c:v", "libx264", "-c:a", "aac", "-ac", "2",
            cls.mp4_stereo
        ]
        subprocess.run(cmd_stereo, check=True)

        # 2. Generate synthetic MP4 with AC3 5.1 surround audio
        cmd_51 = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=24",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1:sample_rate=48000",
            "-f", "lavfi", "-i", "sine=frequency=550:duration=1:sample_rate=48000",
            "-f", "lavfi", "-i", "sine=frequency=660:duration=1:sample_rate=48000",
            "-f", "lavfi", "-i", "sine=frequency=770:duration=1:sample_rate=48000",
            "-f", "lavfi", "-i", "sine=frequency=880:duration=1:sample_rate=48000",
            "-f", "lavfi", "-i", "sine=frequency=990:duration=1:sample_rate=48000",
            "-filter_complex", "[1:a][2:a][3:a][4:a][5:a][6:a]join=inputs=6:channel_layout=5.1[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "libx264", "-c:a", "ac3",
            cls.mp4_surround
        ]
        subprocess.run(cmd_51, check=True)

        # 3. Generate synthetic MKV with H.264 video and AC3 5.1 English audio
        cmd_mkv = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=duration=1:size=640x360:rate=24",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1:sample_rate=48000",
            "-c:v", "libx264", "-c:a", "ac3", "-ac", "6",
            "-metadata:s:a:0", "language=eng",
            cls.mkv_source
        ]
        subprocess.run(cmd_mkv, check=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_format_channel_layout_label(self):
        """Verifies channel count and layout conversions to user-facing labels."""
        self.assertEqual(format_channel_layout_label(1, "mono"), "Mono 1.0")
        self.assertEqual(format_channel_layout_label(2, "stereo"), "Estéreo 2.0")
        self.assertEqual(format_channel_layout_label(2, ""), "Estéreo 2.0")
        self.assertEqual(format_channel_layout_label(6, "5.1(side)"), "Surround 5.1")
        self.assertEqual(format_channel_layout_label(6, "5.1"), "Surround 5.1")
        self.assertEqual(format_channel_layout_label(8, "7.1"), "Surround 7.1")
        self.assertEqual(format_channel_layout_label(4, "quad"), "4 Canais")
        self.assertEqual(format_channel_layout_label(0, ""), "Canais Desconhecidos")

    def test_audio_profile_labels(self):
        """Validates layout and spec formatting on AudioProfile instances."""
        profile = AudioProfile(
            codec="aac",
            channels=2,
            channel_layout="stereo",
            sample_rate=48000,
            bit_rate=192000,
            is_surround=False
        )
        self.assertEqual(profile.layout_label(), "Estéreo 2.0")
        self.assertIn("AAC", profile.spec_label())
        self.assertIn("48.000 Hz", profile.spec_label())
        self.assertIn("192 kbps", profile.spec_label())

    def test_probe_mp4_stereo(self):
        """Deep probing on MP4 file extracts container format, video and stereo AAC audio."""
        info = probe_media_file(self.mp4_stereo)
        self.assertEqual(info.container_format, "mp4")
        self.assertEqual(len(info.video_streams), 1)
        self.assertEqual(len(info.audio_streams), 1)

        v = info.video_streams[0]
        self.assertEqual(v.codec, "h264")
        self.assertEqual(v.width, 320)
        self.assertEqual(v.height, 240)

        a = info.audio_streams[0]
        self.assertEqual(a.codec, "aac")
        self.assertEqual(a.channels, 2)
        self.assertEqual(a.sample_rate, 48000)
        self.assertIsNotNone(a.audio_profile)
        self.assertEqual(a.audio_profile.layout_label(), "Estéreo 2.0")

    def test_probe_mp4_surround_51(self):
        """Deep probing on MP4 with 5.1 channels correctly detects surround configuration."""
        info = probe_media_file(self.mp4_surround)
        self.assertEqual(info.container_format, "mp4")
        self.assertEqual(len(info.audio_streams), 1)

        a = info.audio_streams[0]
        self.assertEqual(a.codec, "ac3")
        self.assertEqual(a.channels, 6)
        self.assertTrue(a.audio_profile.is_surround)
        self.assertEqual(a.audio_profile.layout_label(), "Surround 5.1")

    def test_extract_audio_lossless_stream_copy(self):
        """Demuxing from MP4 executes direct stream copy (-c:a copy) without recoding."""
        out_dir = os.path.join(self.temp_dir, "extracted")
        res = extract_audio_lossless(self.mp4_stereo, track_index=1, output_dir=out_dir)

        self.assertTrue(res.is_direct_copy, "Standard AAC must be extracted via direct stream copy")
        self.assertEqual(res.codec, "aac")
        self.assertTrue(os.path.isfile(res.output_path))
        self.assertGreater(os.path.getsize(res.output_path), 0)
        self.assertTrue(res.output_path.endswith(".m4a"))

    def test_build_mkvmerge_hybrid_command(self):
        """Validates command assembly for MKV video + MP4/extracted audio."""
        cmd = build_mkvmerge_hybrid_command(
            video_mkv="/movies/video_uhd.mkv",
            audio_source="/tmp/extracted_audio.m4a",
            offset_ms=-125.0,
            output_path="/movies/output_synced.mkv",
            video_track_id=0,
            target_audio_track_id=0,
            target_audio_language="por",
            target_audio_name="Português (Brasil)",
            keep_original_audio=True,
            ref_audio_track_id=1,
            original_audio_language="eng",
            original_audio_name="Original English"
        )

        self.assertIn("mkvmerge", cmd[0])
        self.assertIn("-o", cmd)
        self.assertIn("/movies/output_synced.mkv", cmd)
        self.assertIn("--video-tracks", cmd)
        self.assertIn("0", cmd)
        self.assertIn("--audio-tracks", cmd)
        self.assertIn("--sync", cmd)
        # With normalized sign contract: offset_ms = -125.0 implies container delay = -(-125) = +125ms
        self.assertIn("0:125", cmd)
        self.assertIn("--track-name", cmd)
        self.assertIn("0:Português (Brasil)", cmd)
        self.assertIn("/tmp/extracted_audio.m4a", cmd)
        self.assertIn("/movies/video_uhd.mkv", cmd)

    def test_review_gate_acoustic_audit_display(self):
        """Review Gate displays acoustic audit card, origin tags, and contextual channel alert."""
        v_stream = StreamMetadata(
            id=0, codec="hevc", channels=0, sample_rate=0, fps=24.0,
            duration_ms=60000.0, language="und", is_default=True,
            track_type="video", width=3840, height=2160, container_format="mkv"
        )
        cand_v = StreamCandidate(file_path=self.mkv_source, stream=v_stream, score=100.0)

        # Target dubbed audio is Stereo (2.0) from MP4
        a_tgt_stream = StreamMetadata(
            id=1, codec="aac", channels=2, sample_rate=48000, fps=0.0,
            duration_ms=60000.0, language="por", is_default=True,
            track_type="audio", channel_layout="stereo", container_format="mp4",
            audio_profile=AudioProfile("aac", 2, "stereo", 48000, 192000, False)
        )
        cand_tgt = StreamCandidate(file_path=self.mp4_stereo, stream=a_tgt_stream, score=90.0)

        # Reference English audio is Surround 5.1 (6 channels) from MKV
        a_ref_stream = StreamMetadata(
            id=1, codec="ac3", channels=6, sample_rate=48000, fps=0.0,
            duration_ms=60000.0, language="eng", is_default=True,
            track_type="audio", channel_layout="5.1", container_format="mkv",
            audio_profile=AudioProfile("ac3", 6, "5.1", 48000, 640000, True)
        )
        cand_ref = StreamCandidate(file_path=self.mkv_source, stream=a_ref_stream, score=80.0)

        verdict = AutoMatchVerdict(
            recommended_video=cand_v,
            recommended_target_audio=cand_tgt,
            reference_audio=cand_ref
        )

        zone = UnifiedDropZone()
        zone.show()
        zone.set_verdict(verdict)

        # Audit frame should be displayed
        self.assertFalse(zone.frame_audio_audit.isHidden())
        self.assertIn("MP4 ➔ MKV", zone.lbl_audit_origin.text())
        self.assertEqual(zone.badge_audit_layout.text(), "Estéreo 2.0")
        self.assertIn("AAC", zone.lbl_audit_specs.text())

        # Contextual alert should be displayed informing that dubbing is stereo while original is 5.1
        self.assertFalse(zone.frame_channel_alert.isHidden())
        self.assertIn("Estéreo 2.0", zone.lbl_channel_alert.text())
        self.assertIn("5.1", zone.lbl_channel_alert.text())

        zone.deleteLater()


if __name__ == "__main__":
    unittest.main()
