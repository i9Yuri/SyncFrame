"""Unit tests for deterministic stream evaluation, ranking heuristics, and review gate decisions."""

import unittest
from src.core.models import StreamMetadata
from src.core.inspector import (
    rank_video_streams,
    identify_target_and_ref_audios,
    _get_codec_weight
)


class TestStreamEvaluator(unittest.TestCase):

    def test_codec_efficiency_weights(self):
        self.assertGreater(_get_codec_weight("AV1"), _get_codec_weight("HEVC"))
        self.assertGreater(_get_codec_weight("HEVC"), _get_codec_weight("H.264"))
        self.assertGreater(_get_codec_weight("AVC"), _get_codec_weight("MPEG-2"))

    def test_case_1_4k_eng_vs_1080p_ptbr(self):
        """
        Caso 1:
        Arquivo A: 1080p AVC (H.264), áudio PT-BR (Dublado)
        Arquivo B: 2160p 4K HEVC (H.265), áudio ENG (Original)
        Resultado esperado:
        - Vídeo recomendado: Arquivo B (4K HEVC)
        - Áudio dublado alvo: Arquivo A (PT-BR)
        - Áudio referência: Arquivo B (ENG)
        """
        file_a = "/movies/movie_1080p_ptbr.mkv"
        file_b = "/movies/movie_2160p_remux.mkv"

        # File A streams
        v_a = StreamMetadata(
            id=0, codec="AVC", channels=0, sample_rate=0, fps=23.976,
            duration_ms=7200000.0, language="und", is_default=True,
            track_type="video", width=1920, height=1080, bitrate=8_000_000
        )
        a_a = StreamMetadata(
            id=1, codec="AC-3", channels=6, sample_rate=48000, fps=0.0,
            duration_ms=7200000.0, language="por", is_default=True,
            track_type="audio", title="Dublagem Oficial"
        )

        # File B streams
        v_b = StreamMetadata(
            id=0, codec="HEVC", channels=0, sample_rate=0, fps=23.976,
            duration_ms=7200000.0, language="und", is_default=True,
            track_type="video", width=3840, height=2160, bitrate=25_000_000
        )
        a_b = StreamMetadata(
            id=1, codec="TrueHD", channels=8, sample_rate=48000, fps=0.0,
            duration_ms=7200000.0, language="eng", is_default=True,
            track_type="audio", title="English Original"
        )

        streams_with_files = [
            (file_a, v_a),
            (file_a, a_a),
            (file_b, v_b),
            (file_b, a_b),
        ]

        # 1. Video Ranking
        ranked_videos = rank_video_streams(streams_with_files)
        self.assertEqual(len(ranked_videos), 2)
        best_video = ranked_videos[0]

        self.assertEqual(best_video.file_path, file_b)
        self.assertEqual(best_video.stream.width, 3840)
        self.assertTrue(best_video.is_recommended)
        self.assertEqual(best_video.badge_label, "Melhor Qualidade Detectada")

        # 2. Audio Identification
        target_audio, ref_audio, all_audios, is_ambiguous, reason = identify_target_and_ref_audios(
            streams_with_files,
            chosen_video_file=best_video.file_path
        )

        self.assertFalse(is_ambiguous)
        self.assertIsNotNone(target_audio)
        self.assertEqual(target_audio.file_path, file_a)
        self.assertEqual(target_audio.stream.language, "por")
        self.assertTrue(target_audio.is_recommended)

        self.assertIsNotNone(ref_audio)
        self.assertEqual(ref_audio.file_path, file_b)
        self.assertEqual(ref_audio.stream.language, "eng")

    def test_case_2_identical_resolution_codec_tiebreak(self):
        """
        Caso 2:
        Resoluções idênticas (ambas 1080p).
        Arquivo A: 1080p AVC (H.264)
        Arquivo B: 1080p HEVC (H.265)
        Resultado esperado:
        - Arquivo B vence devido ao codec de compressão mais moderno e eficiente.
        """
        file_a = "/movies/movie_1080p_avc.mkv"
        file_b = "/movies/movie_1080p_hevc.mkv"

        v_a = StreamMetadata(
            id=0, codec="AVC", channels=0, sample_rate=0, fps=24.0,
            duration_ms=5000000.0, language="und", is_default=True,
            track_type="video", width=1920, height=1080, bitrate=10_000_000
        )
        v_b = StreamMetadata(
            id=0, codec="HEVC", channels=0, sample_rate=0, fps=24.0,
            duration_ms=5000000.0, language="und", is_default=True,
            track_type="video", width=1920, height=1080, bitrate=10_000_000
        )

        ranked = rank_video_streams([(file_a, v_a), (file_b, v_b)])
        self.assertEqual(ranked[0].file_path, file_b)
        self.assertGreater(ranked[0].score, ranked[1].score)

    def test_case_3_unspecified_language_safe_fallback(self):
        """
        Caso 3:
        Nenhuma tag explícita de idioma nos áudios ("und").
        Resultado esperado:
        - Não gera exceção não tratada.
        - Sinaliza ambiguidade (is_ambiguous = True) com aviso claro.
        - Fornece fallback seguro escolhendo o áudio da fonte secundária.
        """
        file_video = "/movies/video_source.mkv"
        file_audio = "/movies/dubbed_source.mkv"

        v = StreamMetadata(
            id=0, codec="HEVC", channels=0, sample_rate=0, fps=23.976,
            duration_ms=7200000.0, language="und", is_default=True,
            track_type="video", width=1920, height=1080
        )
        a_vid = StreamMetadata(
            id=1, codec="AAC", channels=2, sample_rate=48000, fps=0.0,
            duration_ms=7200000.0, language="und", is_default=True,
            track_type="audio"
        )
        a_dub = StreamMetadata(
            id=1, codec="AC-3", channels=6, sample_rate=48000, fps=0.0,
            duration_ms=7200000.0, language="und", is_default=True,
            track_type="audio"
        )

        streams = [
            (file_video, v),
            (file_video, a_vid),
            (file_audio, a_dub),
        ]

        target_audio, ref_audio, all_audios, is_ambiguous, reason = identify_target_and_ref_audios(
            streams,
            chosen_video_file=file_video
        )

        self.assertTrue(is_ambiguous)
        self.assertIn("Nenhuma tag", reason)
        self.assertIsNotNone(target_audio)
        self.assertEqual(target_audio.file_path, file_audio)
        self.assertIsNotNone(ref_audio)


if __name__ == "__main__":
    unittest.main()
