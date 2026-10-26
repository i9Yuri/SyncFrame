"""Unit tests for N sources dynamic ingestion, atomic chips for secondary audio tracks, and dropdown highlights."""

import unittest
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QFrame

from src.core.models import (
    StreamMetadata,
    StreamCandidate,
    AudioQualityBadge,
    StreamAuditSummary,
    MediaSourceInfo,
    AutoMatchVerdict
)
from src.core.inspector import (
    evaluate_media_streams,
    build_audio_quality_badge,
    build_stream_audit_summary,
    Inspector
)
from src.ui.components.custom_combobox import DropdownHighlightDelegate, HighlightComboBox
from src.ui.components.stream_review_gate import StreamReviewGate, IngestPanel
from src.ui.components.unified_drop_zone import UnifiedDropZone
from src.ui.style import DARK_THEME_QSS, LIGHT_THEME_QSS

app = QApplication.instance() or QApplication([])


class TestNSourcesAndAtomicChips(unittest.TestCase):
    """Test suite covering N sources dynamic ingestion, atomic micro-chips, and dropdown highlights."""

    def test_evaluate_media_streams_with_three_sources(self):
        """Verifies evaluate_media_streams can ingest N >= 2 sources and pool all streams."""
        v_stream = StreamMetadata(
            id=0, codec="hevc", channels=0, sample_rate=0, fps=23.976, duration_ms=60000.0,
            language="und", is_default=True, track_type="video", width=3840, height=2160
        )
        a_eng_stream = StreamMetadata(
            id=1, codec="truehd", channels=8, sample_rate=48000, fps=0.0, duration_ms=60000.0,
            language="eng", is_default=True, track_type="audio", channel_layout="7.1", is_immersive=True
        )
        a_por_stream = StreamMetadata(
            id=2, codec="eac3", channels=6, sample_rate=48000, fps=0.0, duration_ms=60000.0,
            language="por", is_default=False, track_type="audio", channel_layout="5.1"
        )
        a_jap_stream = StreamMetadata(
            id=3, codec="flac", channels=2, sample_rate=48000, fps=0.0, duration_ms=60000.0,
            language="jpn", is_default=False, track_type="audio", channel_layout="stereo"
        )

        source_video = [v_stream, a_eng_stream]
        source_dub = [a_por_stream]
        source_extra = [a_jap_stream]

        # Call with 3 sources
        verdict = evaluate_media_streams(source_video, source_dub, source_extra)

        self.assertIsInstance(verdict, AutoMatchVerdict)
        self.assertEqual(verdict.recommended_video.stream.id, 0)
        self.assertTrue(verdict.recommended_video.is_best_quality)
        self.assertEqual(verdict.recommended_target_audio.stream.id, 2)
        self.assertTrue(verdict.recommended_target_audio.is_best_quality)

        # All 3 audio streams should be represented across target and alternatives
        all_found_ids = {verdict.recommended_target_audio.stream.id}
        for alt in verdict.alternative_audios:
            all_found_ids.add(alt.stream.id)
        if verdict.reference_audio:
            all_found_ids.add(verdict.reference_audio.stream.id)

        self.assertIn(1, all_found_ids, "English reference audio must be found")
        self.assertIn(2, all_found_ids, "Portuguese dubbing audio must be found")
        self.assertIn(3, all_found_ids, "Japanese audio from 3rd source must be pooled")

    def test_build_audio_quality_badge_and_summary(self):
        """Verifies helper methods produce structured dataclasses with correct fields."""
        s = StreamMetadata(
            id=5, codec="truehd", channels=8, sample_rate=48000, fps=0.0, duration_ms=120000.0,
            language="eng", is_default=True, track_type="audio", channel_layout="7.1",
            is_immersive=True, bitrate=4800000, title="Atmos 7.1 Studio Master"
        )
        cand = StreamCandidate(file_path="/movies/film.mkv", stream=s, score=98.0, is_best_quality=True)

        badge = build_audio_quality_badge(cand)
        self.assertIsInstance(badge, AudioQualityBadge)
        self.assertEqual(badge.language, "ENG")
        self.assertEqual(badge.brand_format, "DOLBY ATMOS")
        self.assertEqual(badge.channels_desc, "7.1")
        self.assertEqual(badge.sample_rate_hz, 48000)
        self.assertEqual(badge.bit_rate_kbps, 4800)
        self.assertEqual(badge.codec_name, "TRUEHD")
        self.assertEqual(badge.source_filename, "film.mkv")
        self.assertEqual(badge.track_id, 5)
        self.assertTrue(badge.is_best_option)

        summary = build_stream_audit_summary(cand, container_format="mkv")
        self.assertIsInstance(summary, StreamAuditSummary)
        self.assertEqual(summary.container, "MKV Nativo")
        self.assertEqual(summary.audio_profile, "DOLBY ATMOS")
        self.assertEqual(summary.codec, "TRUEHD")
        self.assertEqual(summary.sample_rate, "48.000 Hz")
        self.assertEqual(summary.bit_rate, "4800 kbps")

    def test_dropdown_highlight_delegate_and_combobox(self):
        """Verifies HighlightComboBox and DropdownHighlightDelegate integration."""
        combo = HighlightComboBox()
        s_best = StreamMetadata(
            id=1, codec="truehd", channels=8, sample_rate=48000, fps=0.0, duration_ms=0.0,
            language="eng", is_default=True, track_type="audio", channel_layout="7.1"
        )
        cand_best = StreamCandidate(file_path="best.mkv", stream=s_best, is_best_quality=True)

        s_regular = StreamMetadata(
            id=2, codec="aac", channels=2, sample_rate=48000, fps=0.0, duration_ms=0.0,
            language="por", is_default=False, track_type="audio", channel_layout="stereo"
        )
        cand_regular = StreamCandidate(file_path="regular.mkv", stream=s_regular, is_best_quality=False)

        combo.addItem("Best Stream", userData=cand_best)
        combo.addItem("Regular Stream", userData=cand_regular)

        self.assertEqual(combo.count(), 2)
        delegate = combo.itemDelegate()
        self.assertIsInstance(delegate, DropdownHighlightDelegate)

        from PySide6.QtWidgets import QStyleOptionViewItem
        opt = QStyleOptionViewItem()
        hint = delegate.sizeHint(opt, combo.model().index(0, 0))
        self.assertGreaterEqual(hint.height(), 36)

    def test_render_secondary_audio_item_atomic_chips(self):
        """Verifies modular card rendering with atomic micro-chips."""
        gate = StreamReviewGate()
        badge_data = AudioQualityBadge(
            language="ENG",
            brand_format="DOLBY ATMOS",
            channels_desc="7.1.4",
            sample_rate_hz=48000,
            bit_rate_kbps=640,
            codec_name="E-AC-3",
            source_filename="Sample_Movie.mkv",
            track_id=3,
            is_best_option=True,
            title="Spatial Audio"
        )

        card = gate.render_secondary_audio_item(badge_data)
        self.assertIsInstance(card, QFrame)
        self.assertEqual(card.property("class"), "secondaryTrackCard")

        # Find checkbox
        chk = card.findChild(QCheckBox)
        self.assertIsNotNone(chk)
        self.assertEqual(chk.objectName(), "chkSecondary_3")
        self.assertTrue(chk.isChecked())

        # Check micro-chips
        labels = card.findChildren(QLabel)
        texts = [l.text() for l in labels]
        self.assertIn("ENG", texts)
        self.assertIn("DOLBY ATMOS", texts)
        self.assertIn("7.1.4", texts)
        self.assertIn("E-AC-3", texts)
        self.assertIn("48.000 Hz • 640 kbps", texts)
        self.assertIn("RECOMENDADO", texts)

        classes = [l.property("class") for l in labels]
        self.assertIn("atomicChip", classes)
        self.assertIn("atomicChipBest", classes)

        # Verify geometric continuity and fixed dimensions
        self.assertEqual(card.height(), 34)
        for l in labels:
            if l.property("class") in ("atomicChip", "atomicChipBest"):
                self.assertEqual(l.height(), 20)
                self.assertEqual(l.alignment(), Qt.AlignCenter)

        # Verify rounded corner tokens in stylesheets
        self.assertIn("border-radius: 9px;", DARK_THEME_QSS)
        self.assertIn("border-radius: 10px;", DARK_THEME_QSS)
        self.assertIn("border-radius: 16px;", DARK_THEME_QSS)

    def test_update_channel_audit_tags(self):
        """Verifies structured deduplicated update_channel_audit_tags."""
        gate = StreamReviewGate()
        summary = StreamAuditSummary(
            container="MKV Nativo",
            audio_profile="DTS-HD MA 7.1",
            channels="Surround 7.1",
            codec="DTS-HD MA",
            sample_rate="48.000 Hz",
            bit_rate="3500 kbps"
        )

        gate.update_channel_audit_tags(summary)
        self.assertEqual(gate.lbl_audit_origin.text(), "MKV Nativo")
        self.assertEqual(gate.badge_audit_layout.text(), "DTS-HD MA 7.1")
        expected_specs = "Codec: DTS-HD MA • Canais: Surround 7.1 • Frequência: 48.000 Hz • Taxa de Bits: 3500 kbps"
        self.assertEqual(gate.lbl_audit_specs.text(), expected_specs)

    def test_dynamic_source_count_update(self):
        """Verifies update_source_count_badge with 3, 5, and N sources."""
        gate = StreamReviewGate()
        gate.update_source_count_badge(3)
        self.assertEqual(gate.chip_sources_count.text(), "3 / 3 FONTES")

        gate.update_source_count_badge(5)
        self.assertEqual(gate.chip_sources_count.text(), "5 / 5 FONTES")

    def test_unified_drop_zone_dynamic_n_sources(self):
        """Verifies UnifiedDropZone renders dynamic cards for N sources and cleans up on reset."""
        drop_zone = UnifiedDropZone()

        s1 = MediaSourceInfo(file_path="/movies/video_imax.mkv", role_label="REFERÊNCIA DE VÍDEO", summary="30 GB • 23.976 fps", is_video_source=True)
        s2 = MediaSourceInfo(file_path="/movies/audio_dub.mp4", role_label="ÁUDIO DUBLADO", summary="1.2 GB • 5.1 • 48000 Hz", is_video_source=False)
        s3 = MediaSourceInfo(file_path="/movies/video_openmatte.mkv", role_label="VÍDEO ALTERNATIVO", summary="18 GB • 23.976 fps", is_video_source=True)
        s4 = MediaSourceInfo(file_path="/movies/soundtrack.flac", role_label="FONTE ADICIONAL", summary="400 MB [FLAC]", is_video_source=False)

        # Ingest 3 sources
        drop_zone.update_sources_view([s1, s2, s3])
        self.assertEqual(drop_zone.chip_sources_count.text(), "3 / 3 FONTES")
        self.assertEqual(len(drop_zone.dynamic_source_cards), 1)
        self.assertEqual(drop_zone.lbl_v_filename.text(), "video_imax.mkv")
        self.assertEqual(drop_zone.lbl_a_filename.text(), "audio_dub.mp4")
        self.assertFalse(drop_zone.card_file_a.isHidden())

        # Ingest 4 sources
        drop_zone.update_sources_view([s1, s2, s3, s4])
        self.assertEqual(drop_zone.chip_sources_count.text(), "4 / 4 FONTES")
        self.assertEqual(len(drop_zone.dynamic_source_cards), 2)

        # Reset cleans up dynamic cards
        drop_zone.reset()
        self.assertEqual(drop_zone.chip_sources_count.text(), "0 / 0 FONTES")
        self.assertEqual(len(drop_zone.dynamic_source_cards), 0)
        self.assertFalse(drop_zone.card_file_a.isHidden())

    def test_unified_drop_zone_combo_video_three_videos(self):
        """Verifies combo_video populates all video tracks across all files."""
        drop_zone = UnifiedDropZone()
        v1 = StreamCandidate(
            file_path="/movies/f1.mkv",
            stream=StreamMetadata(id=0, codec="hevc", channels=0, sample_rate=0, fps=23.976, duration_ms=60000.0, language="und", is_default=True, width=3840, height=2160, track_type="video", container_format="mkv")
        )
        v2 = StreamCandidate(
            file_path="/movies/f2.mkv",
            stream=StreamMetadata(id=0, codec="h264", channels=0, sample_rate=0, fps=60.0, duration_ms=60000.0, language="und", is_default=True, width=1920, height=1080, track_type="video", container_format="mkv")
        )
        v3 = StreamCandidate(
            file_path="/movies/f3.mkv",
            stream=StreamMetadata(id=0, codec="h264", channels=0, sample_rate=0, fps=23.976, duration_ms=60000.0, language="und", is_default=True, width=1920, height=1080, track_type="video", container_format="mkv")
        )
        a1 = StreamCandidate(
            file_path="/movies/f2.mkv",
            stream=StreamMetadata(id=1, codec="ac3", channels=6, sample_rate=48000, fps=0.0, duration_ms=60000.0, language="por", is_default=False, track_type="audio", container_format="mkv")
        )

        verdict = AutoMatchVerdict(
            recommended_video=v1,
            alternative_videos=[v2, v3],
            recommended_target_audio=a1,
            alternative_audios=[],
            reference_audio=None
        )

        drop_zone.loaded_files = ["/movies/f1.mkv", "/movies/f2.mkv", "/movies/f3.mkv"]
        drop_zone.set_verdict(verdict)

        self.assertEqual(drop_zone.chip_sources_count.text(), "3 / 3 FONTES")
        self.assertEqual(drop_zone.combo_video.count(), 3)
        self.assertEqual(len(drop_zone.dynamic_source_cards), 1)


if __name__ == "__main__":
    unittest.main()
