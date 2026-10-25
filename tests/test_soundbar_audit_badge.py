"""Unit tests for SoundbarAuditBadge, SmoothFadeTooltip, and 7.1.4 immersive audit engine."""

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtCore import QPoint, Qt, QEvent
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QApplication

from src.core.models import (
    StreamMetadata,
    StreamCandidate,
    AutoMatchVerdict,
    ImmersiveAuditResult
)
from src.core.inspector import audit_immersive_capabilities
from src.ui.components.soundbar_audit_badge import SoundbarAuditBadge, SmoothFadeTooltip
from src.ui.main_window import SyncFrameMainWindow
from src.ui.components.unified_drop_zone import UnifiedDropZone

app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)


def make_audio_metadata(
    codec: str,
    channels: int,
    sample_rate: int = 48000,
    title: str = "",
    channel_layout: str = "",
    is_immersive: bool = False,
    spatial_label: str = "",
    is_suspicious_transcode: bool = False
) -> StreamMetadata:
    return StreamMetadata(
        id=1,
        codec=codec,
        channels=channels,
        sample_rate=sample_rate,
        fps=0.0,
        duration_ms=60000.0,
        language="por",
        is_default=True,
        track_type="audio",
        title=title,
        channel_layout=channel_layout,
        is_immersive=is_immersive,
        spatial_label=spatial_label,
        is_suspicious_transcode=is_suspicious_transcode
    )


class TestSoundbarAuditBadge(unittest.TestCase):
    """Rigorous tests for 7.1.4 soundbar audit engine and reactive badge component."""

    def test_audit_optimal_truehd_atmos(self):
        """Verifies TrueHD with Dolby Atmos yields optimal status."""
        meta = make_audio_metadata(
            codec="truehd",
            channels=8,
            title="Dolby Atmos",
            is_immersive=True,
            spatial_label="TRUEHD ATMOS"
        )
        res = audit_immersive_capabilities(meta)
        self.assertEqual(res.status, "optimal")
        self.assertIn("Atmos 7.1.4 Ativo", res.title)
        self.assertIn("Mixagem original", res.description)
        self.assertIn("7.1.4", res.suggestion)

    def test_audit_optimal_eac3_joc_atmos(self):
        """Verifies E-AC-3 JOC yields optimal status."""
        meta = make_audio_metadata(
            codec="eac3",
            channels=6,
            title="Dolby Digital Plus with Dolby Atmos",
            is_immersive=True,
            spatial_label="5.1 ATMOS"
        )
        res = audit_immersive_capabilities(meta)
        self.assertEqual(res.status, "optimal")
        self.assertIn("Atmos 7.1.4 Ativo", res.title)

    def test_audit_optimal_dtsx(self):
        """Verifies DTS:X yields optimal status."""
        meta = make_audio_metadata(
            codec="dts",
            channels=8,
            title="DTS:X Master Audio",
            spatial_label="7.1 DTS-HD"
        )
        res = audit_immersive_capabilities(meta)
        self.assertEqual(res.status, "optimal")
        self.assertIn("7.1.4 Ativo", res.title)

    def test_audit_optimal_discrete_71(self):
        """Verifies 8-channel discrete layout yields optimal status."""
        meta = make_audio_metadata(
            codec="flac",
            channels=8,
            channel_layout="7.1"
        )
        res = audit_immersive_capabilities(meta)
        self.assertEqual(res.status, "optimal")
        self.assertIn("7.1", res.title)

    def test_audit_suboptimal_conventional_51(self):
        """Verifies conventional AC-3 5.1 yields suboptimal attention."""
        meta = make_audio_metadata(
            codec="ac3",
            channels=6,
            channel_layout="5.1(side)"
        )
        res = audit_immersive_capabilities(meta)
        self.assertEqual(res.status, "suboptimal")
        self.assertIn("Surround 5.1 Convencional", res.title)
        self.assertIn("Sem canais de teto dedicados", res.description)
        self.assertIn("TrueHD/Atmos", res.suggestion)

    def test_audit_suboptimal_stereo_20(self):
        """Verifies stereo 2.0 yields suboptimal attention."""
        meta = make_audio_metadata(
            codec="aac",
            channels=2,
            channel_layout="stereo"
        )
        res = audit_immersive_capabilities(meta)
        self.assertEqual(res.status, "suboptimal")
        self.assertIn("Estéreo 2.0 Reduzido", res.title)
        self.assertIn("emulação estéreo reduzida", res.description)

    def test_audit_suboptimal_mono_10(self):
        """Verifies mono 1.0 yields suboptimal attention."""
        meta = make_audio_metadata(
            codec="aac",
            channels=1,
            channel_layout="mono"
        )
        res = audit_immersive_capabilities(meta)
        self.assertEqual(res.status, "suboptimal")
        self.assertIn("Mono 1.0", res.title)

    def test_audit_suboptimal_compressed_transcode(self):
        """Verifies multitrack AAC or suspicious transcode yields compressed transcode diagnosis."""
        meta = make_audio_metadata(
            codec="aac",
            channels=6,
            is_suspicious_transcode=True
        )
        res = audit_immersive_capabilities(meta)
        self.assertEqual(res.status, "suboptimal")
        self.assertIn("Multicanal Comprimido", res.title)
        self.assertIn("dinâmica e graves atenuados", res.description)

    def test_audit_stream_candidate_unwrapping(self):
        """Ensures StreamCandidate instances are transparently unwrapped."""
        meta = make_audio_metadata(codec="ac3", channels=6)
        cand = StreamCandidate(stream=meta, file_path="/tmp/test.mkv")
        res = audit_immersive_capabilities(cand)
        self.assertEqual(res.status, "suboptimal")

    def test_audit_none_fallback(self):
        """Ensures None stream yields safe suboptimal fallback."""
        res = audit_immersive_capabilities(None)
        self.assertEqual(res.status, "suboptimal")
        self.assertIn("Nenhuma Faixa Selecionada", res.title)

    def test_badge_dimensions_and_painting(self):
        """Verifies SoundbarAuditBadge geometry, states, and paint cycles."""
        badge = SoundbarAuditBadge()
        try:
            self.assertEqual(badge.width(), 24)
            self.assertEqual(badge.height(), 24)
            self.assertEqual(badge.cursor().shape(), Qt.PointingHandCursor)

            # Test optimal
            opt_res = ImmersiveAuditResult(
                status="optimal",
                title="JBL Bar 1000: Atmos 7.1.4 Ativo",
                description="Mixagem original.",
                suggestion="Aproveitamento pleno."
            )
            badge.set_audit_result(opt_res)
            self.assertEqual(badge.audit_result, opt_res)
            badge.repaint()

            # Test suboptimal
            sub_res = ImmersiveAuditResult(
                status="suboptimal",
                title="JBL Bar 1000: Surround 5.1 Convencional",
                description="Sem canais de teto.",
                suggestion="Selecione Atmos."
            )
            badge.set_audit_result(sub_res)
            self.assertEqual(badge.audit_result, sub_res)
            badge.repaint()

            # Theme switching
            badge.set_theme_mode("light")
            self.assertEqual(badge.current_theme, "light")
            badge.repaint()

            badge.set_theme_mode("dark")
            self.assertEqual(badge.current_theme, "dark")
            badge.repaint()
        finally:
            badge.deleteLater()

    def test_smooth_fade_tooltip_properties_and_display(self):
        """Verifies SmoothFadeTooltip frameless behavior, animation parameters, and positioning."""
        tooltip = SmoothFadeTooltip()
        try:
            self.assertTrue(tooltip.windowFlags() & Qt.ToolTip)
            self.assertTrue(tooltip.windowFlags() & Qt.FramelessWindowHint)
            self.assertEqual(tooltip.fade_anim.duration(), 120)

            res = ImmersiveAuditResult(
                status="optimal",
                title="JBL Bar 1000: Atmos 7.1.4 Ativo",
                description="Mixagem original.",
                suggestion="Aproveitamento pleno."
            )
            tooltip.display_at(QPoint(100, 200), res)
            self.assertEqual(tooltip.lbl_title.text(), res.title)
            self.assertEqual(tooltip.lbl_desc.text(), res.description)
            self.assertEqual(tooltip.lbl_sug.text(), res.suggestion)

            tooltip.hide_tooltip()
            tooltip.hide_immediately()
            self.assertFalse(tooltip.isVisible())
        finally:
            tooltip.deleteLater()

    def test_main_window_integration_and_reactivity(self):
        """Verifies MainWindow hosts badge_soundbar and reacts to audio selection changes."""
        win = SyncFrameMainWindow()
        try:
            self.assertTrue(hasattr(win, "badge_soundbar"))
            self.assertIsNotNone(win.badge_soundbar)
            self.assertEqual(win.badge_soundbar.width(), 24)
            self.assertEqual(win.badge_soundbar.height(), 24)

            # Test reactivity to track change signal
            meta_atmos = make_audio_metadata(
                codec="truehd",
                channels=8,
                title="Dolby Atmos",
                is_immersive=True,
                spatial_label="TRUEHD ATMOS"
            )
            cand_atmos = StreamCandidate(stream=meta_atmos, file_path="/tmp/v.mkv")
            win.drop_zone.primary_audio_changed.emit(cand_atmos)
            self.assertIsNotNone(win.badge_soundbar.audit_result)
            self.assertEqual(win.badge_soundbar.audit_result.status, "optimal")

            # Switch to AC-3 5.1
            meta_51 = make_audio_metadata(codec="ac3", channels=6)
            cand_51 = StreamCandidate(stream=meta_51, file_path="/tmp/v.mkv")
            win.drop_zone.primary_audio_changed.emit(cand_51)
            self.assertEqual(win.badge_soundbar.audit_result.status, "suboptimal")
            self.assertIn("Surround 5.1", win.badge_soundbar.audit_result.title)

            # Test reset clears audit
            win._on_reset_requested()
            self.assertIsNone(win.badge_soundbar.audit_result)
        finally:
            win.close()


if __name__ == "__main__":
    unittest.main()
