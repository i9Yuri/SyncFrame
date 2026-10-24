"""Unit tests validating precision slider, workspace layout manager, floating dock, and end-to-end pipeline."""

import os
import unittest
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QApplication, QGridLayout, QWidget, QFrame

from src.ui.components.log_drawer import FloatingDockWidget
from src.ui.components.sync_controls import DampedSlider, SliderSensitivityController, SyncControls
from src.ui.main_window import SyncFrameMainWindow
from src.ui.workspace_layout import WorkspaceLayoutManager
from src.ui.workers.unified_pipeline_worker import UnifiedPipelineWorker
from src.core.models import RemuxJob

app = QApplication.instance() or QApplication([])


class TestEndToEndWorkspacePipeline(unittest.TestCase):
    def setUp(self):
        self.window = SyncFrameMainWindow()

    def tearDown(self):
        self.window.close()
        # Clean test QSettings
        settings = QSettings("SyncFrame", "TestWorkspaceLayout")
        settings.clear()

    def test_slider_sensitivity_controller_contract(self):
        """Validates SliderSensitivityController modes, step_ms, and scale factors."""
        slider = DampedSlider(Qt.Horizontal)
        controller = SliderSensitivityController(slider)

        self.assertEqual(controller.mode, "normal")
        self.assertEqual(controller.step_ms, 10)
        self.assertEqual(controller.scale_factor, 1.0)
        self.assertEqual(controller["mode"], "normal")
        self.assertEqual(controller["step_ms"], 10)

        controller.set_mode("fine")
        self.assertEqual(controller.mode, "fine")
        self.assertEqual(controller.step_ms, 1)
        self.assertEqual(controller.scale_factor, 0.25)
        self.assertEqual(slider.singleStep(), 1)

        controller.set_mode("coarse")
        self.assertEqual(controller.mode, "coarse")
        self.assertEqual(controller.step_ms, 50)
        self.assertEqual(controller.scale_factor, 2.5)
        self.assertEqual(slider.singleStep(), 50)

        d = controller.to_dict()
        self.assertEqual(d["mode"], "coarse")
        self.assertEqual(d["step_ms"], 50)
        self.assertEqual(d["scale_factor"], 2.5)

    def test_sync_controls_segmented_stepper(self):
        """Verifies segmented pill buttons update sensitivity mode in SyncControls."""
        controls = SyncControls()
        self.assertTrue(hasattr(controls, "stepper_group"))
        self.assertTrue(hasattr(controls, "btn_sens_fine"))
        self.assertTrue(hasattr(controls, "btn_sens_normal"))
        self.assertTrue(hasattr(controls, "btn_sens_coarse"))

        controls.btn_sens_fine.click()
        self.assertEqual(controls.sensitivity_controller.mode, "fine")
        self.assertEqual(controls.slider.singleStep(), 1)
        self.assertEqual(controls.btn_sens_fine.property("active"), "true")
        self.assertEqual(controls.btn_sens_normal.property("active"), "false")

        controls.btn_sens_coarse.click()
        self.assertEqual(controls.sensitivity_controller.mode, "coarse")
        self.assertEqual(controls.slider.singleStep(), 50)
        self.assertEqual(controls.btn_sens_coarse.property("active"), "true")

    def test_floating_dock_widget_contract(self):
        """Verifies FloatingDockWidget toggle_expansion, zero emojis, and logging."""
        dock = FloatingDockWidget()
        self.assertEqual(dock.height(), FloatingDockWidget.RESTING_HEIGHT)
        self.assertFalse(dock.is_expanded)

        # Check clean typography (strictly zero emojis)
        self.assertEqual(dock.btn_toggle.text(), "Expandir")
        self.assertEqual(dock.btn_clear.text(), "Limpar")

        # Expansion
        dock.toggle_expansion(True)
        self.assertTrue(dock.is_expanded)
        self.assertEqual(dock.btn_toggle.text(), "Recolher")

        # Collapse
        dock.toggle_expansion(False)
        self.assertFalse(dock.is_expanded)
        self.assertEqual(dock.btn_toggle.text(), "Expandir")

        # Logging
        dock.append_log("Diagnostic event test message")
        self.assertEqual(dock.event_count, 1)
        self.assertIn("Diagnostic event test message", dock.text_edit.toPlainText())

        dock.clear_logs()
        self.assertEqual(dock.event_count, 0)
        self.assertEqual(dock.text_edit.toPlainText(), "")

    def test_workspace_layout_manager_save_and_restore(self):
        """Verifies WorkspaceLayoutManager persists and restores grid positions with validation."""
        grid_parent = QWidget()
        grid = QGridLayout(grid_parent)

        card_a = QFrame()
        card_b = QFrame()
        widgets_map = {"card_a": card_a, "card_b": card_b}

        grid.addWidget(card_a, 0, 0, 1, 1)
        grid.addWidget(card_b, 0, 1, 1, 1)

        mgr = WorkspaceLayoutManager(parent_grid=grid, settings_group="TestWorkspaceLayout", widgets_map=widgets_map)
        mgr.save_layout(widgets_map)

        # Restore into new grid
        new_grid_parent = QWidget()
        new_grid = QGridLayout(new_grid_parent)
        restored = mgr.restore_layout(new_grid)
        self.assertTrue(restored)

        # Toggle edit mode
        mgr.toggle_edit_mode(True)
        self.assertTrue(mgr.is_edit_mode)
        self.assertEqual(card_a.property("editMode"), "true")

        mgr.toggle_edit_mode(False)
        self.assertFalse(mgr.is_edit_mode)
        self.assertEqual(card_a.property("editMode"), "false")

    def test_workspace_layout_manager_corrupted_fallback(self):
        """Verifies WorkspaceLayoutManager falls back gracefully when coordinates are out of bounds."""
        settings = QSettings("SyncFrame", "TestWorkspaceCorrupted")
        settings.clear()
        settings.beginGroup("cards")
        settings.beginGroup("drop_zone")
        settings.setValue("row", 999)  # Out of bounds (> 10)
        settings.setValue("col", 999)
        settings.endGroup()
        settings.endGroup()
        settings.setValue("has_custom_layout", True)
        settings.sync()

        grid_parent = QWidget()
        grid = QGridLayout(grid_parent)
        mgr = WorkspaceLayoutManager(parent_grid=grid, settings_group="TestWorkspaceCorrupted", widgets_map=self.window.widgets_map)

        restored = mgr.restore_layout(grid)
        self.assertFalse(restored)  # Must return False and fall back to default
        settings.clear()

    def test_main_window_execute_pipeline_contract(self):
        """Verifies MainWindow provides execute_end_to_end_pipeline() method."""
        self.assertTrue(hasattr(self.window, "execute_end_to_end_pipeline"))
        self.assertTrue(callable(self.window.execute_end_to_end_pipeline))

    def test_main_window_topbar_pill_sizes(self):
        """Verifies topbar pill tags and buttons auto-fit to content."""
        self.assertTrue(hasattr(self.window, "btn_edit_mode"))
        self.assertTrue(hasattr(self.window, "btn_theme"))
        self.assertTrue(hasattr(self.window, "badge_v"))
        self.window._update_topbar_pill_sizes()

        fm_btn = self.window.btn_edit_mode.fontMetrics()
        expected_w = fm_btn.horizontalAdvance(self.window.btn_edit_mode.text()) + 28
        self.assertEqual(self.window.btn_edit_mode.width(), expected_w)

    def test_pipeline_worker_signal_contracts(self):
        """Verifies correlation_started, correlation_finished, and remux_finished signals exist on worker."""
        job = RemuxJob(
            output_path="/tmp/test_out.mkv",
            video_file="/tmp/test_vid.mkv",
            target_audio_file="/tmp/test_aud.mkv",
            offset_ms=0.0,
            stretch_ratio=1.0,
            video_track_id=1,
            target_audio_track_id=1,
            ref_audio_track_id=1,
            keep_original_audio=True
        )
        worker = UnifiedPipelineWorker(job)
        self.assertTrue(hasattr(worker, "correlation_started"))
        self.assertTrue(hasattr(worker, "correlation_finished"))
        self.assertTrue(hasattr(worker, "remux_finished"))


if __name__ == "__main__":
    unittest.main()
