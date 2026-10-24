"""Universal test suite asserting 100% rounded corners and geometric continuity across SyncFrame."""

import re
import unittest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.ui.style import (
    DARK_THEME_QSS,
    LIGHT_THEME_QSS,
    get_theme_stylesheet,
    StyleEngine,
    apply_universal_rounded_tokens,
    CustomStyleEngine,
    enforce_universal_pill_radius,
    get_clean_badge_style,
    get_role_badge_style,
    get_action_chip_style,
    get_pill_button_style,
    get_compact_dropzone_style,
    get_telemetry_card_style
)
from src.ui.components.completion_dialog import CompletionDialog
from src.ui.components.correlation_view import CorrelationView
from src.ui.components.stream_selector_modal import StreamSelectorModal
from src.ui.components.sync_controls import SensitivitySelectorWidget, SyncControls
from src.ui.main_window import SyncFrameMainWindow
from src.ui.workspace_layout import WorkspaceLayoutManager
from src.core.models import AutoMatchVerdict, StreamCandidate, StreamMetadata

app = QApplication.instance()
if not app:
    app = QApplication([])


class TestAllRoundedCorners(unittest.TestCase):
    """Rigorous geometric test verifying zero sharp corners across all UI components."""

    def test_dark_and_light_stylesheets_have_no_zero_radius(self):
        """Verifies that border-radius: 0 or border-radius: 0px is nowhere in the styles."""
        for name, qss in [("dark", DARK_THEME_QSS), ("light", LIGHT_THEME_QSS)]:
            self.assertNotIn("border-radius: 0;", qss, f"Found border-radius: 0 in {name} theme")
            self.assertNotIn("border-radius: 0px;", qss, f"Found border-radius: 0px in {name} theme")

    def test_universal_widget_rounding_coverage(self):
        """Asserts all core widget classes have explicit rounded corner specifications."""
        for name, qss in [("dark", DARK_THEME_QSS), ("light", LIGHT_THEME_QSS)]:
            self.assertIn("QFrame {", qss)
            self.assertIn("border-radius: 24px;", qss)

            self.assertIn("QDialog, QMessageBox", qss)
            self.assertIn("border-radius: 28px;", qss)

            self.assertIn("QToolTip {", qss)
            self.assertIn("border-radius: 12px;", qss)

            self.assertIn("QMenu {", qss)
            self.assertIn("border-radius: 18px;", qss)

            self.assertIn("QScrollBar:vertical {", qss)
            self.assertIn("QScrollBar:horizontal {", qss)
            self.assertIn("border-radius: 4px;", qss)

            self.assertIn("QComboBox QAbstractItemView {", qss)
            self.assertIn("border-radius: 16px;", qss)

            self.assertIn("QLineEdit.outPath", qss)
            self.assertIn("border-radius: 999px;", qss)

            self.assertIn("QPlainTextEdit {", qss)
            self.assertIn("border-radius: 20px;", qss)

            self.assertIn("QProgressBar {", qss)
            self.assertIn("border-radius: 7px;", qss)

            self.assertIn("QSlider::handle:horizontal {", qss)
            self.assertIn("border-radius: 9px;", qss)

    def test_completion_dialog_has_rounded_geometry(self):
        """Verifies CompletionDialog has rounded styles on dialog and all children."""
        dlg = CompletionDialog(output_file_path="/movies/output.mkv")
        sheet = dlg.styleSheet()
        self.assertIn("border-radius: 28px;", sheet)
        self.assertIn("border-radius: 18px;", sheet)
        self.assertIn("border-radius: 999px;", sheet)
        self.assertEqual(dlg.glyph_badge.width(), 36)
        self.assertEqual(dlg.glyph_badge.height(), 36)

    def test_stream_selector_modal_has_rounded_geometry(self):
        """Verifies StreamSelectorModal has rounded corners on modal surface and cards."""
        v_stream = StreamMetadata(
            id=0,
            codec="hevc",
            channels=0,
            sample_rate=0,
            fps=23.976,
            duration_ms=60000.0,
            language="und",
            is_default=True,
            track_type="video",
            width=3840,
            height=2160,
        )
        a_stream = StreamMetadata(
            id=1,
            codec="ac3",
            channels=6,
            sample_rate=48000,
            fps=0.0,
            duration_ms=60000.0,
            language="por",
            is_default=False,
            track_type="audio",
            channel_layout="5.1",
        )
        v_cand = StreamCandidate(file_path="movie.mkv", stream=v_stream, score=90.0, badge_label="4K UHD")
        a_cand = StreamCandidate(file_path="audio.mkv", stream=a_stream, score=85.0, badge_label="5.1 PT-BR")

        verdict = AutoMatchVerdict(
            recommended_video=v_cand,
            recommended_target_audio=a_cand,
            reference_audio=a_cand,
            is_ambiguous=True,
            ambiguity_reason="Teste de alerta"
        )
        modal = StreamSelectorModal(verdict=verdict)
        sheet = modal.styleSheet()
        self.assertIn("border-radius: 28px;", sheet)
        self.assertIn("border-radius: 24px;", sheet)
        self.assertIn("border-radius: 999px;", sheet)
        self.assertIn("border-radius: 16px;", sheet)

    def test_correlation_view_paint_clipping(self):
        """Verifies CorrelationView paints without error using rounded clipping path."""
        cv = CorrelationView()
        cv.resize(400, 200)
        cv.set_data([0.1, 0.4, 0.9, 0.3, 0.1], offset_ms=-250.0, confidence=0.88)
        # Calling repaint triggers paintEvent with clip path
        cv.repaint()
        self.assertEqual(cv.peak_offset_ms, -250.0)

    def test_workspace_layout_edit_mode_retains_rounded_borders(self):
        """Verifies entering edit mode in layout manager maintains rounded corners (border-radius: 32px)."""
        cv = CorrelationView()
        lm = WorkspaceLayoutManager(widgets_map={"acoustic": cv})
        lm.toggle_edit_mode(True)
        self.assertIn("border-radius: 32px;", cv.styleSheet())
        lm.toggle_edit_mode(False)
        self.assertNotIn("dashed", cv.styleSheet())

    def test_style_engine_and_helpers_rounded_contracts(self):
        """Verifies helper functions produce rounded styles."""
        self.assertIn("border-radius: 14px;", get_clean_badge_style())
        self.assertIn("border-radius: 14px;", get_role_badge_style("role"))
        self.assertIn("border-radius: 14px;", get_action_chip_style("action"))
        self.assertIn("border-radius: 999px;", get_pill_button_style(is_primary=True))
        self.assertIn("border-radius: 999px;", get_pill_button_style(is_primary=False))
        self.assertIn("border-radius: 24px;", get_compact_dropzone_style())
        self.assertIn("border-radius: 22px;", get_telemetry_card_style())

        self.assertTrue(len(StyleEngine.apply_universal_rounded_tokens("dark")) > 1000)
        self.assertTrue(len(apply_universal_rounded_tokens("light")) > 1000)

    def test_custom_style_engine_contract(self):
        """Verifies CustomStyleEngine.enforce_universal_pill_radius contract."""
        dark_qss = CustomStyleEngine.enforce_universal_pill_radius("dark")
        light_qss = enforce_universal_pill_radius("light")
        self.assertIn("border-radius: 999px;", dark_qss)
        self.assertIn("border-radius: 999px;", light_qss)
        self.assertIn("QFrame#sensitivitySelector", dark_qss)
        self.assertIn("QFrame#sensitivitySelector", light_qss)

    def test_sensitivity_selector_widget_contract(self):
        """Verifies SensitivitySelectorWidget functionality and step switching contract."""
        widget = SensitivitySelectorWidget()
        steps_recorded = []
        widget.step_changed.connect(steps_recorded.append)

        self.assertEqual(widget.current_step, 10)
        widget.set_sensitivity_step(1)
        self.assertEqual(widget.current_step, 1)
        self.assertEqual(steps_recorded, [1])

        widget.set_sensitivity_step(50)
        self.assertEqual(widget.current_step, 50)
        self.assertEqual(steps_recorded, [1, 50])

        # Test SyncControls integration
        sc = SyncControls()
        self.assertTrue(hasattr(sc, "sensitivity_selector"))
        self.assertTrue(hasattr(sc, "btn_reset"))
        self.assertEqual(sc.btn_reset.property("class"), "pill")
        self.assertEqual(sc.btn_reset.objectName(), "btnResetOffset")

    def test_main_window_topbar_actions_and_pipeline_contract(self):
        """Verifies MainWindow topbar setup, edit mode removal, pill auto-sizing and start_sync_pipeline."""
        win = SyncFrameMainWindow()
        self.assertTrue(hasattr(win, "setup_topbar_actions"))
        self.assertTrue(callable(win.setup_topbar_actions))
        self.assertTrue(hasattr(win, "start_sync_pipeline"))
        self.assertTrue(callable(win.start_sync_pipeline))
        self.assertTrue(hasattr(win, "active_pipeline_worker"))

        # Setup topbar actions
        win.setup_topbar_actions()

        # Inoperant edit mode button must be hidden from topbar
        self.assertFalse(win.btn_edit_mode.isVisible())

        # Topbar pills must have fixed 34px height
        self.assertEqual(win.pill_workspace.height(), 34)
        self.assertEqual(win.btn_theme.height(), 34)
        self.assertEqual(win.badge_v.height(), 34)

        # Pill workspace must be wider than text alone due to green dot and padding
        fm_ws = win.chip_workspace.fontMetrics()
        min_expected = fm_ws.horizontalAdvance(win.chip_workspace.text()) + 28
        self.assertGreaterEqual(win.pill_workspace.width(), min_expected)
        win.close()


if __name__ == "__main__":
    unittest.main()
