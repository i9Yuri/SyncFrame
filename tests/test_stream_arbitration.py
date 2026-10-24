"""Unit tests for audio stream arbitration, acoustic quality evaluation, and mkvmerge exclusion flags."""

import unittest
from src.core.models import StreamMetadata, AudioQualityScore, StreamArbitrationResult
from src.core.inspector import (
    evaluate_audio_quality,
    arbitrate_duplicate_language_streams,
    get_codec_tier
)
from src.core.remuxer import build_mkvmerge_exclusion_flags, build_mkvmerge_hybrid_command


class TestStreamArbitration(unittest.TestCase):
    """Test suite for deterministic audio track quality evaluation and duplicate language replacement."""

    def setUp(self):
        # Audio PT 2.0 AAC 128 kbps (Typical lower quality stream)
        self.stream_pt_2ch_aac = StreamMetadata(
            id=2,
            codec="aac",
            channels=2,
            sample_rate=48000,
            fps=0.0,
            duration_ms=7200000.0,
            language="por",
            is_default=False,
            track_type="audio",
            title="Dublagem 2.0",
            bitrate=128000
        )

        # Audio PT 5.1 AC3 640 kbps (Typical higher quality surround stream)
        self.stream_pt_6ch_ac3 = StreamMetadata(
            id=1,
            codec="ac3",
            channels=6,
            channel_layout="5.1(side)",
            sample_rate=48000,
            fps=0.0,
            duration_ms=7200000.0,
            language="por",
            is_default=True,
            track_type="audio",
            title="Dublagem 5.1",
            bitrate=640000
        )

        # Audio PT 7.1 TrueHD (Master lossless stream)
        self.stream_pt_8ch_truehd = StreamMetadata(
            id=3,
            codec="truehd",
            channels=8,
            channel_layout="7.1",
            sample_rate=48000,
            fps=0.0,
            duration_ms=7200000.0,
            language="por",
            is_default=False,
            track_type="audio",
            title="Dublagem 7.1 TrueHD",
            bitrate=3500000
        )

        # Video stream 4K
        self.stream_video_4k = StreamMetadata(
            id=0,
            codec="hevc",
            channels=0,
            sample_rate=0,
            fps=23.976,
            duration_ms=7200000.0,
            language="und",
            is_default=True,
            track_type="video",
            width=3840,
            height=2160
        )

        # English reference audio
        self.stream_ref_eng = StreamMetadata(
            id=1,
            codec="dts",
            channels=6,
            sample_rate=48000,
            fps=0.0,
            duration_ms=7200000.0,
            language="eng",
            is_default=True,
            track_type="audio"
        )

    def test_codec_tier_ranking(self):
        """Validates preservation tier ranking for diverse audio codecs."""
        self.assertEqual(get_codec_tier("flac"), 5)
        self.assertEqual(get_codec_tier("truehd"), 5)
        self.assertEqual(get_codec_tier("pcm_s24le"), 5)
        self.assertEqual(get_codec_tier("eac3"), 4)
        self.assertEqual(get_codec_tier("ac3"), 4)
        self.assertEqual(get_codec_tier("opus"), 4)
        self.assertEqual(get_codec_tier("aac"), 3)
        self.assertEqual(get_codec_tier("mp3"), 2)
        self.assertEqual(get_codec_tier("unknown_codec"), 1)

    def test_evaluate_audio_quality_priorities(self):
        """Validates that Priority 1 (Channels) > Priority 2 (Codec) > Priority 3 (Bitrate)."""
        score_2ch = evaluate_audio_quality(self.stream_pt_2ch_aac)
        score_6ch = evaluate_audio_quality(self.stream_pt_6ch_ac3)
        score_8ch = evaluate_audio_quality(self.stream_pt_8ch_truehd)

        # Priority 1: 8ch > 6ch > 2ch
        self.assertGreater(score_8ch.total_score, score_6ch.total_score)
        self.assertGreater(score_6ch.total_score, score_2ch.total_score)

        # Priority 2: Within 2 channels, FLAC (Tier 5) > AC3 (Tier 4) > AAC (Tier 3) > MP3 (Tier 2)
        s_2ch_flac = StreamMetadata(id=1, codec="flac", channels=2, sample_rate=48000, fps=0, duration_ms=0, language="por", is_default=False, bitrate=0)
        s_2ch_ac3 = StreamMetadata(id=2, codec="ac3", channels=2, sample_rate=48000, fps=0, duration_ms=0, language="por", is_default=False, bitrate=384000)
        s_2ch_aac = StreamMetadata(id=3, codec="aac", channels=2, sample_rate=48000, fps=0, duration_ms=0, language="por", is_default=False, bitrate=320000)
        s_2ch_mp3 = StreamMetadata(id=4, codec="mp3", channels=2, sample_rate=48000, fps=0, duration_ms=0, language="por", is_default=False, bitrate=320000)

        score_flac = evaluate_audio_quality(s_2ch_flac)
        score_ac3 = evaluate_audio_quality(s_2ch_ac3)
        score_aac = evaluate_audio_quality(s_2ch_aac)
        score_mp3 = evaluate_audio_quality(s_2ch_mp3)

        self.assertGreater(score_flac.total_score, score_ac3.total_score)
        self.assertGreater(score_ac3.total_score, score_aac.total_score)
        self.assertGreater(score_aac.total_score, score_mp3.total_score)

        # Priority 3: Within same channels and codec, higher bitrate wins
        s_aac_128 = StreamMetadata(id=5, codec="aac", channels=2, sample_rate=48000, fps=0, duration_ms=0, language="por", is_default=False, bitrate=128000)
        s_aac_320 = StreamMetadata(id=6, codec="aac", channels=2, sample_rate=48000, fps=0, duration_ms=0, language="por", is_default=False, bitrate=320000)
        self.assertGreater(evaluate_audio_quality(s_aac_320).total_score, evaluate_audio_quality(s_aac_128).total_score)

    def test_evaluate_audio_quality_missing_bitrate_fallback(self):
        """Ensures missing or null bitrate doesn't raise exception and falls back to channels/codec tier."""
        s_null_br = StreamMetadata(id=1, codec="aac", channels=2, sample_rate=48000, fps=0, duration_ms=0, language="por", is_default=False, bitrate=None)
        s_zero_br = StreamMetadata(id=2, codec="aac", channels=2, sample_rate=48000, fps=0, duration_ms=0, language="por", is_default=False, bitrate=0)

        score_null = evaluate_audio_quality(s_null_br)
        score_zero = evaluate_audio_quality(s_zero_br)

        self.assertEqual(score_null.bit_rate, 0)
        self.assertEqual(score_zero.bit_rate, 0)
        self.assertAlmostEqual(score_null.total_score, score_zero.total_score, places=3)

    def test_arbitration_simulation_1_superior_external_replaces_inferior_base(self):
        """
        Simulation 1:
        Base Video (File A): 4K Video + Original English + Inferior PT 2.0 AAC (ID 2).
        External (File B): Superior PT 5.1 AC3 (ID 1).
        Expected: Selects External PT 5.1, marks Base PT ID 2 as discarded, is_replacement=True.
        """
        base_streams = [self.stream_video_4k, self.stream_ref_eng, self.stream_pt_2ch_aac]
        external_streams = [self.stream_pt_6ch_ac3]

        result = arbitrate_duplicate_language_streams(base_streams, external_streams, lang_code="por")

        self.assertTrue(result.is_replacement)
        self.assertEqual(result.selected_target_audio.id, self.stream_pt_6ch_ac3.id)
        self.assertEqual(result.selected_target_audio.codec, "ac3")
        self.assertEqual(result.selected_target_audio.channels, 6)
        self.assertIn(self.stream_pt_2ch_aac.id, result.discarded_audio_ids)
        self.assertIn("Substituindo faixa local", result.reason)

    def test_arbitration_simulation_2_superior_base_notifies_user(self):
        """
        Simulation 2:
        Base Video (File A): 4K Video + Superior PT 5.1 AC3 (ID 1).
        External (File B): Inferior PT 2.0 AAC (ID 2).
        Expected: Keeps Base PT 5.1, discarded_audio_ids empty, is_replacement=False, notification reason.
        """
        base_streams = [self.stream_video_4k, self.stream_pt_6ch_ac3]
        external_streams = [self.stream_pt_2ch_aac]

        result = arbitrate_duplicate_language_streams(base_streams, external_streams, lang_code="por")

        self.assertFalse(result.is_replacement)
        self.assertEqual(result.selected_target_audio.id, self.stream_pt_6ch_ac3.id)
        self.assertEqual(result.discarded_audio_ids, [])
        self.assertIn("já possui fidelidade técnica superior", result.reason)

    def test_arbitration_simulation_3_equal_metrics_fallback(self):
        """
        Simulation 3:
        Identical metrics on both sources (e.g. both 5.1 AC3 640 kbps).
        Expected: Keeps external track by default, marks duplicate base track for discard.
        """
        base_pt_dup = StreamMetadata(
            id=2, codec="ac3", channels=6, sample_rate=48000, fps=0, duration_ms=0, language="por", is_default=False, bitrate=640000
        )
        base_streams = [self.stream_video_4k, self.stream_ref_eng, base_pt_dup]
        external_streams = [self.stream_pt_6ch_ac3]

        result = arbitrate_duplicate_language_streams(base_streams, external_streams, lang_code="por")

        self.assertTrue(result.is_replacement)
        self.assertEqual(result.selected_target_audio.id, self.stream_pt_6ch_ac3.id)
        self.assertIn(base_pt_dup.id, result.discarded_audio_ids)
        self.assertIn("Métricas equivalentes", result.reason)

    def test_build_mkvmerge_exclusion_flags(self):
        """Validates mkvmerge command flag construction for discarded audio tracks."""
        # Empty list -> no flags
        self.assertEqual(build_mkvmerge_exclusion_flags([]), [])

        # Single stream ID
        flags_single = build_mkvmerge_exclusion_flags([2])
        self.assertEqual(flags_single, ["--audio-tracks", "!2"])

        # Multiple stream IDs
        flags_multi = build_mkvmerge_exclusion_flags([2, 4])
        self.assertEqual(flags_multi, ["--audio-tracks", "!2,4"])

    def test_build_mkvmerge_hybrid_command_with_exclusion(self):
        """Validates that build_mkvmerge_hybrid_command integrates exclusion flags."""
        cmd = build_mkvmerge_hybrid_command(
            video_mkv="/movies/video.mkv",
            audio_source="/movies/audio.mka",
            offset_ms=0.0,
            output_path="/movies/out.mkv",
            video_track_id=0,
            target_audio_track_id=0,
            keep_original_audio=True,
            ref_audio_track_id=1,
            discarded_audio_ids=[2]
        )

        self.assertIn("--audio-tracks", cmd)
        self.assertIn("!2", cmd)
        self.assertIn("/movies/video.mkv", cmd)
        self.assertIn("/movies/audio.mka", cmd)


if __name__ == "__main__":
    unittest.main()
