"""Unit test suite for FloatingActionDock, EventLogPopover, VersionInfoPopover and Topbar isolation."""

import unittest
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout

from src.ui.components.floating_action_dock import FloatingActionDock, DockItemConfig
from src.ui.components.event_log_popover import EventLogPopover
from src.ui.components.version_info_popover import VersionInfoPopover
from src.ui.main_window import SyncFrameMainWindow


class TestFloatingActionDock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_dock_item_config(self):
        cfg = DockItemConfig(
            id="test_tool",
            icon_svg="terminal",
            label="Test Tool",
            tooltip_text="Tooltip for test tool",
            badge_count=5
        )
        self.assertEqual(cfg.id, "test_tool")
        self.assertEqual(cfg.icon_svg, "terminal")
        self.assertEqual(cfg.label, "Test Tool")
        self.assertEqual(cfg.tooltip_text, "Tooltip for test tool")
        self.assertEqual(cfg.badge_count, 5)

    def test_floating_action_dock_initialization_and_fit_content(self):
        parent = QWidget()
        parent.resize(1024, 768)
        dock = FloatingActionDock(parent)

        self.assertEqual(dock.height(), 52)
        self.assertIn("event_log", dock.buttons)
        self.assertIn("check_updates", dock.buttons)
        self.assertIn("theme_toggle", dock.buttons)
        self.assertIn("version_info", dock.buttons)

        # Expected width: 16 (pad) + 4*40 (buttons) + 3*12 (gaps) + 16 (pad) = 228
        expected_w = (16 * 2) + (4 * 40) + (3 * 12)
        self.assertEqual(dock.width(), expected_w)

    def test_dock_reposition_math(self):
        parent = QWidget()
        parent.resize(1000, 700)
        dock = FloatingActionDock(parent)
        dock.reposition(1000, 700)

        expected_x = (1000 - dock.width()) // 2
        expected_y = 700 - dock.height() - 20
        self.assertEqual(dock.x(), expected_x)
        self.assertEqual(dock.y(), expected_y)

    def test_badge_counter_updates(self):
        parent = QWidget()
        dock = FloatingActionDock(parent)

        dock.update_badge_count("event_log", 12)
        btn = dock.buttons.get("event_log")
        self.assertIsNotNone(btn)
        self.assertEqual(btn.config.badge_count, 12)

    def test_event_log_popover_append_clear_and_memory_limit(self):
        popover = EventLogPopover()
        self.assertEqual(popover.event_count, 0)
        self.assertEqual(popover.badge_count.text(), "00 EVENTOS")

        # Append messages
        popover.append_log("Initialization finished.")
        self.assertEqual(popover.event_count, 1)
        self.assertEqual(popover.badge_count.text(), "01 EVENTOS")
        self.assertIn("Initialization finished.", popover.text_edit.toPlainText())

        # Test clear
        popover.clear_logs()
        self.assertEqual(popover.event_count, 0)
        self.assertEqual(popover.badge_count.text(), "00 EVENTOS")
        self.assertEqual(popover.text_edit.toPlainText(), "")

        # Test memory bounds: max 1000 blocks
        for i in range(1050):
            popover.append_log(f"Log entry #{i}")

        self.assertLessEqual(popover.text_edit.document().blockCount(), 1000)
        self.assertEqual(popover.event_count, 1050)

    def test_version_info_popover_system_info(self):
        popover = VersionInfoPopover()
        popover.set_system_info(
            app_version="v1.2.0",
            tool_versions={
                "ffmpeg": "6.1.1",
                "mkvmerge": "82.0",
                "mpv": "0.37.0"
            }
        )
        self.assertEqual(popover.chip_app_v.text(), "SyncFrame v1.2.0")
        self.assertIn("FFmpeg 6.1.1", popover.lbl_engines_val.text())
        self.assertIn("MKVToolNix 82.0", popover.lbl_engines_val.text())
        self.assertIn("MPV 0.37.0", popover.lbl_engines_val.text())

    def test_topbar_sanitization_and_isolation(self):
        win = SyncFrameMainWindow()
        win.resize(1024, 768)

        # Inspect topbar layout: action buttons on the right must be removed (sanitized topbar)
        tb_layout = win.topbar.layout()
        self.assertIsInstance(tb_layout, QHBoxLayout)

        # Confirm btn_theme, pill_workspace, badge_v, btn_check_updates are NOT in tb_layout
        self.assertEqual(tb_layout.indexOf(win.btn_theme), -1)
        self.assertTrue(win.btn_theme.isHidden())
        self.assertEqual(tb_layout.indexOf(win.pill_workspace), -1)
        self.assertEqual(tb_layout.indexOf(win.badge_v), -1)
        self.assertEqual(tb_layout.indexOf(win.btn_check_updates), -1)

        # Confirm floating dock hosts the theme toggle button and switches themes
        self.assertTrue(hasattr(win, "floating_dock"))
        self.assertIsInstance(win.floating_dock, FloatingActionDock)
        self.assertIn("theme_toggle", win.floating_dock.buttons)
        theme_btn = win.floating_dock.buttons["theme_toggle"]
        self.assertEqual(theme_btn.toolTip(), "Modo Claro")

        # Test click toggle via dock
        theme_btn.click()
        self.assertEqual(win.current_theme, "light")
        self.assertEqual(theme_btn.toolTip(), "Modo Escuro")
        theme_btn.click()
        self.assertEqual(win.current_theme, "dark")
        self.assertEqual(theme_btn.toolTip(), "Modo Claro")

        win.floating_dock.reposition(win.width(), win.height())
        self.assertEqual(win.floating_dock.height(), 52)

        win.close()

    def test_event_log_popover_expanded_dimensions_and_escape(self):
        popover = EventLogPopover()
        self.assertEqual(popover.width(), 820)
        self.assertEqual(popover.height(), 520)

        # Show and test escape dismissal
        popover.show()
        self.assertTrue(popover.isVisible())

        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent
        esc_event = QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier)
        popover.keyPressEvent(esc_event)
        self.assertFalse(popover.isVisible())

    def test_dock_hover_depth_and_sibling_dimming(self):
        parent = QWidget()
        parent.resize(800, 600)
        dock = FloatingActionDock(parent)

        btn_log = dock.buttons["event_log"]
        btn_up = dock.buttons["check_updates"]
        btn_info = dock.buttons["version_info"]

        # Initially all resting at 1.0
        self.assertEqual(btn_log.scaleFactor, 1.0)
        self.assertEqual(btn_log.buttonOpacity, 1.0)
        self.assertEqual(btn_up.buttonOpacity, 1.0)
        self.assertEqual(btn_info.buttonOpacity, 1.0)

        # Trigger hover on btn_log
        dock.on_button_hover_enter(btn_log)
        self.assertEqual(btn_log._scale_anim.endValue(), 1.35)
        self.assertEqual(btn_log._opacity_anim.endValue(), 1.0)
        self.assertEqual(btn_up._opacity_anim.endValue(), 0.45)
        self.assertEqual(btn_info._opacity_anim.endValue(), 0.45)

        # Trigger hover leave
        dock.on_button_hover_leave(btn_log)
        self.assertEqual(btn_log._scale_anim.endValue(), 1.0)
        self.assertEqual(btn_log._opacity_anim.endValue(), 1.0)
        self.assertEqual(btn_up._opacity_anim.endValue(), 1.0)
        self.assertEqual(btn_info._opacity_anim.endValue(), 1.0)

    def test_dock_popover_click_toggle(self):
        parent = QWidget()
        parent.resize(1000, 700)
        parent.show()
        dock = FloatingActionDock(parent)
        dock.reposition(1000, 700)

        # 1st click: shows popover
        dock._on_event_log_clicked()
        self.assertTrue(dock.log_popover.isVisible())

        # 2nd click: hides popover
        dock._on_event_log_clicked()
        self.assertFalse(dock.log_popover.isVisible())


if __name__ == "__main__":
    unittest.main()
