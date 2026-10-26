"""Unit tests for secondary audio ranking, DLNA metadata args, channel audit technical summary, and UI ergonomics."""

import os
import unittest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QSpacerItem

from src.core.models import (
    AudioStreamDetail,
    StreamMetadata,
    StreamCandidate,
    format_immersive_profile_label
)
from src.core.inspector import Inspector, rank_secondary_audio_streams, compute_stream_quality_score
from src.core.remuxer import Remuxer, generate_dlna_track_args
from src.ui.components.stream_review_gate import StreamReviewGate, IngestPanel
from src.ui.components.sync_controls import SyncControls
from src.ui.style import DARK_THEME_QSS, LIGHT_THEME_QSS

app = QApplication.instance()
if not app:
    app = QApplication([])


class TestSecondaryRankingAndDLNA(unittest.TestCase):
    """Verifies audiophile ranking heuristics, DLNA metadata generation, and UI compliance."""

    def test_secondary_audio_ranking_tiers(self):
        """Verifies 4-tier ranking and strictly top-1 original stream auto-selection."""
        s_truehd = AudioStreamDetail(
            id=1,
            codec="truehd",
            channels=8,
            channel_layout="7.1",
            is_immersive=True,
            language="eng",
            title="TrueHD Atmos 7.1",
            bitrate=4800000
        )
        s_dtshd = AudioStreamDetail(
            id=2,
            codec="dts",
            channels=8,
            channel_layout="7.1",
            language="eng",
            title="DTS-HD MA 7.1",
            bitrate=3500000
        )
        s_ac3 = AudioStreamDetail(
            id=3,
            codec="ac3",
            channels=6,
            channel_layout="5.1",
            language="eng",
            title="AC-3 5.1",
            bitrate=640000
        )
        s_aac = AudioStreamDetail(
            id=4,
            codec="aac",
            channels=2,
            channel_layout="stereo",
            language="eng",
            title="AAC 2.0",
            bitrate=192000
        )

        # TrueHD Atmos (Tier 1) should outscore AC-3 (Tier 3)
        self.assertGreater(
            compute_stream_quality_score(s_truehd),
            compute_stream_quality_score(s_ac3)
        )
        self.assertGreater(
            compute_stream_quality_score(s_dtshd),
            compute_stream_quality_score(s_ac3)
        )
        self.assertGreater(
            compute_stream_quality_score(s_ac3),
            compute_stream_quality_score(s_aac)
        )

        # Ranking unordered list
        ranked = Inspector.rank_secondary_audio_streams([s_aac, s_ac3, s_truehd, s_dtshd])

        # Top item must be s_truehd (or s_dtshd, both Tier 1)
        top_stream, is_top_rec = ranked[0]
        self.assertTrue(is_top_rec, "Top stream in Tier 1 should be recommended")
        self.assertEqual(top_stream.id, s_truehd.id)

        # Exactly 1 stream must be recommended
        rec_count = sum(1 for _, rec in ranked if rec)
        self.assertEqual(rec_count, 1, "Strictly top-1 stream must be recommended")

        # Lower-tier streams must be unselected by default
        for stream, is_rec in ranked[1:]:
            self.assertFalse(is_rec, f"Stream {stream.codec} {stream.channels}ch should be unselected by default")

    def test_dlna_track_args_generation(self):
        """Verifies Matroska container track metadata flags for DLNA/UPnP (BubbleUPnP fix)."""
        # Primary Portuguese dubbing track
        dub_track = AudioStreamDetail(
            id=1,
            codec="ac3",
            channels=6,
            channel_layout="5.1",
            language="por",
            title="Dublagem",
            sample_rate=48000,
            bitrate=640000
        )
        dub_args = Remuxer.generate_dlna_track_args(dub_track, is_primary=True)

        self.assertIn("--track-name", dub_args)
        idx_name = dub_args.index("--track-name") + 1
        self.assertEqual(dub_args[idx_name], "1:Português (Dublagem Oficial - AC-3 5.1)")

        self.assertIn("--language", dub_args)
        idx_lang = dub_args.index("--language") + 1
        self.assertEqual(dub_args[idx_lang], "1:por")

        self.assertIn("--track-enabled-flag", dub_args)
        idx_enabled = dub_args.index("--track-enabled-flag") + 1
        self.assertEqual(dub_args[idx_enabled], "1:1")

        self.assertIn("--default-track-flag", dub_args)
        idx_default = dub_args.index("--default-track-flag") + 1
        self.assertEqual(dub_args[idx_default], "1:1")

        self.assertIn("--forced-display-flag", dub_args)
        idx_forced = dub_args.index("--forced-display-flag") + 1
        self.assertEqual(dub_args[idx_forced], "1:0")

        # Secondary English original track
        orig_track = AudioStreamDetail(
            id=2,
            codec="truehd",
            channels=8,
            channel_layout="7.1",
            is_immersive=True,
            language="eng",
            title="Inglês",
            sample_rate=48000,
            bitrate=4800000
        )
        orig_args = Remuxer.generate_dlna_track_args(orig_track, is_primary=False)

        self.assertIn("--track-name", orig_args)
        idx_orig_name = orig_args.index("--track-name") + 1
        self.assertEqual(orig_args[idx_orig_name], "2:Inglês (Original - TrueHD 7.1 Atmos)")

        self.assertIn("--language", orig_args)
        idx_orig_lang = orig_args.index("--language") + 1
        self.assertEqual(orig_args[idx_orig_lang], "2:eng")

        self.assertIn("--track-enabled-flag", orig_args)
        idx_orig_enabled = orig_args.index("--track-enabled-flag") + 1
        self.assertEqual(orig_args[idx_orig_enabled], "2:1")

        self.assertIn("--default-track-flag", orig_args)
        idx_orig_default = orig_args.index("--default-track-flag") + 1
        self.assertEqual(orig_args[idx_orig_default], "2:0")

        self.assertIn("--forced-display-flag", orig_args)
        idx_orig_forced = orig_args.index("--forced-display-flag") + 1
        self.assertEqual(orig_args[idx_orig_forced], "2:0")

    def test_channel_audit_summary_and_badges(self):
        """Verifies technical audit badges and monospace specification strings."""
        gate = StreamReviewGate()

        # Test AC-3 5.1 in MKV native
        track_ac3 = AudioStreamDetail(
            id=1,
            codec="ac3",
            channels=6,
            channel_layout="5.1",
            sample_rate=48000,
            bitrate=640000
        )
        gate.update_channel_audit_summary(track_ac3, container_format="mkv")

        self.assertEqual(gate.lbl_audit_origin.text(), "MKV Nativo")
        self.assertEqual(gate.badge_audit_layout.text(), "DOLBY AUDIO 5.1")
        expected_spec = "Codec: AC-3 • Canais: Surround 5.1 • Frequência: 48.000 Hz • Taxa de Bits: 640 kbps"
        self.assertEqual(gate.lbl_audit_specs.text(), expected_spec)

        # Test Remux container badge
        gate.update_channel_audit_summary(track_ac3, container_format="mp4")
        self.assertEqual(gate.lbl_audit_origin.text(), "MP4 -> MKV Remux")

        # Test TrueHD Atmos 7.1
        track_atmos = AudioStreamDetail(
            id=2,
            codec="truehd",
            channels=8,
            channel_layout="7.1",
            is_immersive=True,
            sample_rate=48000,
            bitrate=4800000
        )
        gate.update_channel_audit_summary(track_atmos, container_format="mkv")
        self.assertEqual(gate.badge_audit_layout.text(), "DOLBY ATMOS")
        self.assertEqual(gate.badge_audit_layout.property("class"), "badgeSignal")

    def test_resulting_output_specs_pills_and_topology(self):
        """Verifies reactive badges, channel topology decomposition, and public contract in resulting specs."""
        gate = StreamReviewGate()

        # 1. 5.1 AC-3 Passthrough
        track_ac3 = AudioStreamDetail(
            id=1,
            codec="ac3",
            channels=6,
            channel_layout="5.1",
            sample_rate=48000,
            bitrate=640000
        )
        specs = gate.update_resulting_specs(track_ac3, {"container": "mkv", "pal_pitch": False})

        self.assertEqual(gate.pill_res_container.text(), "MKV Matroska")
        self.assertEqual(gate.pill_res_mode.text(), "Cópia Direta (Passthrough)")
        self.assertIn("resultingPillGreen", gate.pill_res_mode.property("class"))
        self.assertEqual(gate.pill_res_brand.text(), "DOLBY AUDIO 5.1")
        self.assertIn("resultingPillGreen", gate.pill_res_brand.property("class"))
        self.assertEqual(gate.pill_res_codec.text(), "AC-3")
        self.assertEqual(gate.pill_res_channels.text(), "5.1 Surround (+Subwoofer)")
        self.assertEqual(gate.pill_res_rate.text(), "48.000 Hz")
        self.assertEqual(gate.pill_res_bitrate.text(), "640 kbps")
        self.assertTrue(specs["is_passthrough"])
        self.assertTrue(specs["has_lfe"])

        # 2. PAL pitch restore with FLAC re-encode
        specs_flac = gate.update_resulting_specs(track_ac3, {"container": "mkv", "pal_pitch": True, "audio_codec": "flac"})
        self.assertEqual(gate.pill_res_mode.text(), "Re-encode FLAC (PAL 24fps)")
        self.assertIn("resultingPillAmber", gate.pill_res_mode.property("class"))
        self.assertEqual(gate.pill_res_codec.text(), "FLAC")
        self.assertEqual(gate.pill_res_brand.text(), "FLAC LOSSLESS")
        self.assertFalse(specs_flac["is_passthrough"])

        # 3. PAL pitch restore with Opus re-encode
        specs_opus = gate.update_resulting_specs(track_ac3, {"container": "mkv", "pal_pitch": True, "audio_codec": "opus"})
        self.assertEqual(gate.pill_res_mode.text(), "Re-encode OPUS (PAL 24fps)")
        self.assertEqual(gate.pill_res_codec.text(), "OPUS")
        self.assertEqual(gate.pill_res_brand.text(), "OPUS")

        # 4. TrueHD Atmos 7.1
        track_atmos = AudioStreamDetail(
            id=2,
            codec="truehd",
            channels=8,
            channel_layout="7.1",
            is_immersive=True,
            sample_rate=48000,
            bitrate=4800000
        )
        specs_atmos = gate.update_resulting_specs(track_atmos, {"container": "mkv", "pal_pitch": False})
        self.assertEqual(gate.pill_res_brand.text(), "DOLBY ATMOS")
        self.assertIn("resultingPillSignal", gate.pill_res_brand.property("class"))
        self.assertEqual(gate.pill_res_codec.text(), "TRUEHD")
        self.assertEqual(gate.pill_res_channels.text(), "7.1 Atmos (Surround + Height + Sub)")
        self.assertTrue(specs_atmos["has_lfe"])

        # 5. Explicit Height Layout 7.1.4
        track_714 = AudioStreamDetail(
            id=3,
            codec="eac3",
            channels=12,
            channel_layout="7.1.4",
            is_immersive=True,
            sample_rate=48000,
            bitrate=768000
        )
        specs_714 = gate.update_resulting_specs(track_714, {"container": "mkv", "pal_pitch": False})
        self.assertEqual(gate.pill_res_channels.text(), "7.1.4 Atmos (Surround + Height + Sub)")

        # 6. Stereo 2.0 without LFE and MP4 Remux
        track_stereo = AudioStreamDetail(
            id=4,
            codec="aac",
            channels=2,
            channel_layout="stereo",
            sample_rate=44100,
            bitrate=192000
        )
        specs_stereo = gate.update_resulting_specs(track_stereo, {"container": "mp4", "pal_pitch": False})
        self.assertEqual(gate.pill_res_container.text(), "MKV Remux")
        self.assertEqual(gate.pill_res_channels.text(), "2.0 Estéreo (Sem LFE)")
        self.assertEqual(gate.pill_res_rate.text(), "44.100 Hz")
        self.assertEqual(gate.pill_res_bitrate.text(), "192 kbps")
        self.assertFalse(specs_stereo["has_lfe"])

        # 7. Mono 1.0 without LFE
        track_mono = AudioStreamDetail(
            id=5,
            codec="ac3",
            channels=1,
            channel_layout="mono",
            sample_rate=48000,
            bitrate=128000
        )
        specs_mono = gate.update_resulting_specs(track_mono, {"container": "mkv", "pal_pitch": False})
        self.assertEqual(gate.pill_res_channels.text(), "1.0 Mono (Sem LFE)")
        self.assertFalse(specs_mono["has_lfe"])

        # 8. Empty Fallback State
        specs_empty = gate.update_resulting_specs(None)
        self.assertEqual(gate.pill_res_container.text(), "Nenhum áudio selecionado")
        self.assertFalse(gate.pill_res_mode.isVisible())
        self.assertEqual(specs_empty["container"], "Nenhum áudio selecionado")

    def test_dynamic_source_count_badge(self):
        """Verifies decoupling of '2 / 2 SOURCES' to dynamic 'N / N FONTES'."""
        gate = StreamReviewGate()

        gate.update_source_count_badge(3)
        self.assertEqual(gate.chip_sources_count.text(), "3 / 3 FONTES")

        gate.update_source_count_badge(4)
        self.assertEqual(gate.chip_sources_count.text(), "4 / 4 FONTES")

        panel = IngestPanel()
        panel.update_source_count_badge(2)
        self.assertEqual(panel.chip_sources_count.text(), "2 / 2 FONTES")

    def test_sync_controls_vertical_breathing_space(self):
        """Verifies 16px vertical breathing space between quick steps and telemetry row."""
        ctrl = SyncControls()
        layout = ctrl.layout()
        found_spacing = False
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.spacerItem():
                size_hint = item.spacerItem().sizeHint()
                if size_hint.height() == 16:
                    found_spacing = True
                    break
        self.assertTrue(found_spacing, "Layout must contain 16px vertical spacing before telemetry row")

    def test_secondary_checkbox_styles_and_contrast(self):
        """Verifies that secondary audio styles exist and light mode has high contrast tokens."""
        # Dark theme check
        self.assertIn("QFrame#frameSecondaryAudio", DARK_THEME_QSS)
        self.assertIn("QCheckBox.chkSecondaryAudio", DARK_THEME_QSS)
        self.assertIn("QLabel#lblFsaTitle", DARK_THEME_QSS)
        self.assertIn("QLabel#chipFsaStatus", DARK_THEME_QSS)
        self.assertIn("QLabel#lblAuditSpecs", DARK_THEME_QSS)

        # Light theme check
        self.assertIn("QFrame#frameSecondaryAudio", LIGHT_THEME_QSS)
        self.assertIn("QCheckBox.chkSecondaryAudio", LIGHT_THEME_QSS)
        self.assertIn("QLabel#lblFsaTitle", LIGHT_THEME_QSS)
        self.assertIn("QLabel#chipFsaStatus", LIGHT_THEME_QSS)
        self.assertIn("QLabel#lblAuditSpecs", LIGHT_THEME_QSS)

        # Check QComboBox QAbstractItemView border-radius and item border-radius
        self.assertIn("border-radius: 16px", DARK_THEME_QSS)
        self.assertIn("border-radius: 10px", DARK_THEME_QSS)
        self.assertIn("border-radius: 16px", LIGHT_THEME_QSS)
        self.assertIn("border-radius: 10px", LIGHT_THEME_QSS)

        # Assert frameSecondaryAudio has no dark rectangle artifact (transparent background)
        self.assertIn("QFrame#frameSecondaryAudio {\n    background-color: transparent;\n    border: none;\n}", DARK_THEME_QSS)
        self.assertIn("QFrame#frameSecondaryAudio {\n    background-color: transparent;\n    border: none;\n}", LIGHT_THEME_QSS)


if __name__ == "__main__":
    unittest.main()
