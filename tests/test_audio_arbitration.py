"""Unit tests for audio stream arbitration, spurious bitrate sanitization, immersive Atmos detection, and manual UI track override."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtWidgets import QApplication

from src.core.models import (
    StreamMetadata,
    StreamCandidate,
    AutoMatchVerdict,
    AudioProfile,
)
from src.core.inspector import (
    sanitize_stream_bitrate,
    detect_immersive_audio_metadata,
    calculate_perceptual_audio_score,
    evaluate_audio_quality,
    arbitrate_duplicate_language_streams,
    evaluate_media_streams,
    probe_audio_channels_fast,
)
from src.ui.components.unified_drop_zone import (
    UnifiedDropZone,
    format_audio_dropdown_item,
)

# Initialize single QApplication instance for offscreen tests
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)


class TestAudioArbitration(unittest.TestCase):
    """Test suite validating audio bitrate sanitization, Dolby Atmos audit, perceptual scoring, and UI review gate."""

    def setUp(self):
        self.drop_zone = UnifiedDropZone()

    def tearDown(self):
        self.drop_zone.deleteLater()

    def test_sanitize_stream_bitrate_caps_inflated_aac(self):
        """Validates that a spurious 17 Mbps bitrate on an AAC stream is capped and falls back to nominal standard."""
        # AAC ceiling is 640 kbps; 17,697,000 bps is spurious
        sanitized = sanitize_stream_bitrate(
            raw_bitrate=17_697_000,
            stream_size=0,
            duration_sec=0,
            codec="aac",
            channels=6
        )
        self.assertLessEqual(sanitized, 640_000)
        self.assertEqual(sanitized, 384_000)

    def test_sanitize_stream_bitrate_byte_rate_fallback(self):
        """Validates that physical byte rate calculation is used when stream size and duration are present."""
        # 30 MB in 600 seconds = (30,000,000 * 8) / 600 = 400,000 bps
        sanitized = sanitize_stream_bitrate(
            raw_bitrate=15_000_000,
            stream_size=30_000_000,
            duration_sec=600.0,
            codec="aac",
            channels=6
        )
        self.assertEqual(sanitized, 400_000)

    def test_sanitize_stream_bitrate_preserves_valid_bitrate(self):
        """Validates that authentic broadcast bitrates within theoretical limits are preserved."""
        # 384 kbps AC-3 is valid (ceiling 640 kbps)
        sanitized_ac3 = sanitize_stream_bitrate(
            raw_bitrate=384_000,
            stream_size=0,
            duration_sec=0,
            codec="ac3",
            channels=6
        )
        self.assertEqual(sanitized_ac3, 384_000)

        # 640 kbps E-AC-3 is valid (ceiling 1536 kbps)
        sanitized_eac3 = sanitize_stream_bitrate(
            raw_bitrate=640_000,
            stream_size=0,
            duration_sec=0,
            codec="eac3",
            channels=6
        )
        self.assertEqual(sanitized_eac3, 640_000)

    def test_detect_immersive_audio_metadata(self):
        """Validates detection of Dolby Atmos, E-AC-3 JOC, and spatial multichannels."""
        # Case 1: TrueHD with Atmos in title
        atmos_truehd = {
            "codec_name": "truehd",
            "channels": 8,
            "channel_layout": "7.1",
            "tags": {"title": "Dolby Atmos 7.1 TrueHD"}
        }
        label, is_imm = detect_immersive_audio_metadata(atmos_truehd)
        self.assertTrue(is_imm)
        self.assertEqual(label, "7.1 ATMOS")

        # Case 2: E-AC-3 JOC (profile or title)
        eac3_joc = {
            "codec_name": "eac3",
            "profile": "Dolby Digital Plus with Dolby Atmos",
            "channels": 6,
            "channel_layout": "5.1"
        }
        label, is_imm = detect_immersive_audio_metadata(eac3_joc)
        self.assertTrue(is_imm)
        self.assertEqual(label, "5.1 ATMOS")

        # Case 3: Standard AC-3 5.1
        std_ac3 = {
            "codec_name": "ac3",
            "channels": 6,
            "channel_layout": "5.1(side)"
        }
        label, is_imm = detect_immersive_audio_metadata(std_ac3)
        self.assertFalse(is_imm)
        self.assertEqual(label, "5.1 DOLBY AUDIO")

        # Case 4: Standard AAC 2.0
        std_aac = {
            "codec_name": "aac",
            "channels": 2,
            "channel_layout": "stereo"
        }
        label, is_imm = detect_immersive_audio_metadata(std_aac)
        self.assertFalse(is_imm)
        self.assertEqual(label, "Estéreo 2.0")

    def test_real_world_avengers_arbitration_simulation(self):
        """
        Simulates the real-world case:
        - 4K file: Os.Vingadores.2012.2160p.UHD.mkv
            * Video: HEVC 3840x2160
            * Audio ENG: TrueHD 7.1 (reference)
            * Audio PT: AAC 5.1 with spurious 17 Mbps header (transcoded dubbing)
        - 1080p file: Os.Vingadores.2012.1080p-WOLVERDONFILMES.COM.mkv
            * Video: AVC 1920x1080
            * Audio PT: AC-3 5.1 384 kbps (authentic broadcast dubbing)
            * Audio ENG: AC-3 5.1
        """
        path_4k = "/media/movies/Os.Vingadores.2012.2160p.UHD.mkv"
        path_1080p = "/media/movies/Os.Vingadores.2012.1080p-WOLVERDONFILMES.COM.mkv"

        # 4K Streams
        v_4k = StreamMetadata(
            id=0, codec="hevc", channels=0, sample_rate=0, fps=23.976,
            duration_ms=8570000.0, language="und", is_default=True, track_type="video",
            width=3840, height=2160
        )
        a_eng_truehd = StreamMetadata(
            id=1, codec="truehd", channels=8, channel_layout="7.1", sample_rate=48000,
            fps=0.0, duration_ms=8570000.0, language="eng", is_default=True, track_type="audio",
            bitrate=4500000, spatial_label="7.1 DOLBY AUDIO"
        )
        # Inflated raw bitrate from container format
        sanitized_aac_bitrate = sanitize_stream_bitrate(17_697_000, 0, 8570.0, "aac", 6)
        a_pt_aac_corrupted = StreamMetadata(
            id=2, codec="aac", channels=6, channel_layout="5.1", sample_rate=48000,
            fps=0.0, duration_ms=8570000.0, language="por", is_default=False, track_type="audio",
            bitrate=sanitized_aac_bitrate, is_suspicious_transcode=True, spatial_label="5.1 AAC"
        )

        # 1080p Streams
        v_1080p = StreamMetadata(
            id=0, codec="h264", channels=0, sample_rate=0, fps=23.976,
            duration_ms=8570000.0, language="und", is_default=True, track_type="video",
            width=1920, height=1080
        )
        a_pt_ac3 = StreamMetadata(
            id=1, codec="ac3", channels=6, channel_layout="5.1(side)", sample_rate=48000,
            fps=0.0, duration_ms=8570000.0, language="por", is_default=True, track_type="audio",
            bitrate=384000, spatial_label="5.1 DOLBY AUDIO"
        )
        a_eng_ac3 = StreamMetadata(
            id=2, codec="ac3", channels=6, channel_layout="5.1(side)", sample_rate=48000,
            fps=0.0, duration_ms=8570000.0, language="eng", is_default=False, track_type="audio",
            bitrate=384000
        )

        streams_4k = [v_4k, a_eng_truehd, a_pt_aac_corrupted]
        streams_1080p = [v_1080p, a_pt_ac3, a_eng_ac3]

        # Check perceptual score ranking: AC-3 5.1 must beat AAC 5.1
        score_aac = calculate_perceptual_audio_score(a_pt_aac_corrupted)
        score_ac3 = calculate_perceptual_audio_score(a_pt_ac3)
        self.assertGreater(score_ac3, score_aac, "Authentic broadcast AC-3 5.1 must beat transcoded AAC 5.1")

        # Run arbitration directly
        arb = arbitrate_duplicate_language_streams(streams_4k, streams_1080p, lang_code="por")
        self.assertTrue(arb.is_replacement)
        self.assertEqual(arb.selected_target_audio.id, a_pt_ac3.id)
        self.assertIn(2, arb.discarded_audio_ids)
        self.assertIn("Substituindo faixa local", arb.reason)
        self.assertIn("broadcast autêntico", arb.reason)

        # Run evaluate_media_streams to obtain AutoMatchVerdict
        verdict = evaluate_media_streams(streams_4k, streams_1080p)
        self.assertEqual(verdict.recommended_video.stream.width, 3840)
        self.assertEqual(verdict.recommended_target_audio.stream.codec, "ac3")
        self.assertEqual(verdict.reference_audio.stream.codec, "truehd")
        self.assertIsNotNone(verdict.arbitration_result)
        self.assertTrue(verdict.arbitration_result.is_replacement)

    def test_unified_drop_zone_all_tracks_and_override(self):
        """Validates that UnifiedDropZone loads all audio tracks into combos and enforces conflict validation."""
        path_4k = "/media/movies/Os.Vingadores.2012.2160p.UHD.mkv"
        path_1080p = "/media/movies/Os.Vingadores.2012.1080p-WOLVERDONFILMES.COM.mkv"

        v_cand = StreamCandidate(
            stream=StreamMetadata(id=0, codec="hevc", channels=0, sample_rate=0, fps=23.976,
                                  duration_ms=8570000.0, language="und", is_default=True, track_type="video",
                                  width=3840, height=2160),
            file_path=path_4k
        )
        ref_cand = StreamCandidate(
            stream=StreamMetadata(id=1, codec="truehd", channels=8, channel_layout="7.1", sample_rate=48000,
                                  fps=0.0, duration_ms=8570000.0, language="eng", is_default=True, track_type="audio",
                                  bitrate=4500000, spatial_label="7.1 DOLBY AUDIO"),
            file_path=path_4k
        )
        base_aac_cand = StreamCandidate(
            stream=StreamMetadata(id=2, codec="aac", channels=6, channel_layout="5.1", sample_rate=48000,
                                  fps=0.0, duration_ms=8570000.0, language="por", is_default=False, track_type="audio",
                                  bitrate=384000, spatial_label="5.1 AAC"),
            file_path=path_4k
        )
        ext_ac3_cand = StreamCandidate(
            stream=StreamMetadata(id=1, codec="ac3", channels=6, channel_layout="5.1(side)", sample_rate=48000,
                                  fps=0.0, duration_ms=8570000.0, language="por", is_default=True, track_type="audio",
                                  bitrate=384000, spatial_label="5.1 DOLBY AUDIO"),
            file_path=path_1080p
        )

        verdict = AutoMatchVerdict(
            recommended_video=v_cand,
            alternative_videos=[],
            recommended_target_audio=ext_ac3_cand,
            alternative_audios=[base_aac_cand, ref_cand],
            reference_audio=ref_cand,
            is_ambiguous=False
        )

        self.drop_zone.set_verdict(verdict)

        # Check formatted dropdown items
        item_text = format_audio_dropdown_item(ext_ac3_cand)
        self.assertIn("Trilha #1", item_text)
        self.assertIn("POR", item_text)
        self.assertIn("AC3", item_text)
        self.assertIn("384 kbps", item_text)

        # Both combos must have all 3 audio tracks
        self.assertEqual(self.drop_zone.combo_target_audio.count(), 3)
        self.assertEqual(self.drop_zone.combo_ref_audio.count(), 3)

        # Target audio default is ext_ac3_cand
        self.assertEqual(self.drop_zone.combo_target_audio.currentData(), ext_ac3_cand)
        # Reference audio default is ref_cand
        self.assertEqual(self.drop_zone.combo_ref_audio.currentData(), ref_cand)
        self.assertTrue(self.drop_zone.btn_confirm.isEnabled())
        self.assertFalse(self.drop_zone.frame_channel_alert.isVisible())

        # Simulate user conflicting selection: set target audio to ref_cand
        idx_ref = self.drop_zone.combo_target_audio.findData(ref_cand)
        self.drop_zone.combo_target_audio.setCurrentIndex(idx_ref)

        self.assertFalse(self.drop_zone.frame_channel_alert.isHidden())
        self.assertIn("[AVISO] Seleção conflitante", self.drop_zone.lbl_channel_alert.text())
        self.assertFalse(self.drop_zone.btn_confirm.isEnabled())
        self.assertEqual(self.drop_zone.badge_a_status.text(), "Conflito")

        # Revert conflict by selecting ext_ac3_cand again
        idx_target = self.drop_zone.combo_target_audio.findData(ext_ac3_cand)
        self.drop_zone.combo_target_audio.setCurrentIndex(idx_target)
        self.assertTrue(self.drop_zone.btn_confirm.isEnabled())
        self.assertTrue(self.drop_zone.frame_channel_alert.isHidden())

    @patch("os.path.isfile", return_value=True)
    @patch("subprocess.run")
    def test_fast_channel_probe_fallback(self, mock_subproc, mock_isfile):
        """Validates fast ffmpeg astats channel layout probing fallback."""
        mock_subproc.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="Stream #0:1: Audio: ac3, 48000 Hz, 5.1(side), fltp\nChannel count: 6\n"
        )
        channels, layout = probe_audio_channels_fast("/fake/movie.mkv", stream_index=1)
        self.assertEqual(channels, 6)
        self.assertEqual(layout, "5.1(side)")


if __name__ == "__main__":
    unittest.main()
