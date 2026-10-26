"""Unit tests for PreFlightChecker, PreFlightDialog, DependencyUpdateWorker, and LipSyncController."""

import os
import shutil
import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QProcess, Qt
from PySide6.QtWidgets import QApplication

from src.utils.system_check import PreFlightChecker, PreFlightReport
from src.ui.components.preflight_dialog import PreFlightDialog
from src.ui.components.preview_player import LipSyncController, PreviewPlayer
from src.ui.workers.dependency_update_worker import DependencyUpdateWorker
from src.ui.main_window import SyncFrameMainWindow

app = QApplication.instance()
if not app:
    app = QApplication([])


class TestPreFlightAndUpdater(unittest.TestCase):
    """Rigorous verification of pre-flight checks, background updater, and lip-sync player."""

    def test_preflight_checker_contract(self):
        """Verifies PreFlightChecker.verify_system_binaries returns a valid PreFlightReport."""
        report = PreFlightChecker.verify_system_binaries()
        self.assertIsInstance(report, PreFlightReport)
        self.assertIsInstance(report.is_ready, bool)
        self.assertIsInstance(report.missing_tools, list)
        self.assertIsInstance(report.tool_versions, dict)

        # On the local test host, ffmpeg, ffprobe, mkvmerge, mpv must be present
        self.assertTrue(report.is_ready, f"Missing tools on host: {report.missing_tools}")
        self.assertIn("ffmpeg", report.tool_versions)
        self.assertIn("mkvmerge", report.tool_versions)
        self.assertIn("mpv", report.tool_versions)

    def test_preflight_checker_package_mapping(self):
        """Verifies package mapping for missing dependencies."""
        pkgs = PreFlightChecker.get_package_names(["ffmpeg", "ffprobe", "mkvmerge", "mpv"])
        self.assertIn("ffmpeg", pkgs)
        self.assertIn("mkvtoolnix", pkgs)
        self.assertIn("mpv", pkgs)
        # Deduplication check (ffmpeg and ffprobe both map to ffmpeg)
        self.assertEqual(len(pkgs), 3)

    def test_preflight_checker_missing_behavior(self):
        """Verifies that missing tools produce is_ready = False."""
        with patch("shutil.which", return_value=None):
            report = PreFlightChecker.verify_system_binaries()
            self.assertFalse(report.is_ready)
            self.assertEqual(len(report.missing_tools), 4)

    def test_preflight_dialog_structure(self):
        """Verifies PreFlightDialog modal elements, buttons, and rounded styling."""
        report = PreFlightReport(
            is_ready=False,
            missing_tools=["mkvmerge", "mpv"],
            tool_versions={}
        )
        dlg = PreFlightDialog(report)
        self.assertEqual(dlg.btn_exit.text(), "Sair")
        self.assertEqual(dlg.btn_install.text(), "Instalar Dependências")
        self.assertEqual(dlg.btn_exit.height(), 34)
        self.assertEqual(dlg.btn_install.height(), 34)
        self.assertTrue(dlg.isModal())
        dlg.close()

    def test_dependency_update_worker_contract(self):
        """Verifies DependencyUpdateWorker signals and execution."""
        worker = DependencyUpdateWorker()
        self.assertTrue(hasattr(worker, "audit_finished"))
        self.assertTrue(hasattr(worker, "update_available"))
        self.assertTrue(hasattr(worker, "status_message"))
        self.assertTrue(hasattr(worker, "update_progress"))
        self.assertTrue(hasattr(worker, "update_completed"))

        captured_audit = []
        worker.audit_finished.connect(captured_audit.append)

        # Run worker synchronously
        worker.run()
        self.assertEqual(len(captured_audit), 1)
        res = captured_audit[0]
        self.assertIn("syncframe", res)
        self.assertIn("tools", res)
        self.assertEqual(res["syncframe"]["local_version"], "2.0.0")

    def test_dependency_update_worker_semantic_comparison(self):
        """Verifies semantic version parsing avoids false-positive downgrade notices."""
        from src.ui.workers.dependency_update_worker import parse_semantic_version
        self.assertGreater(parse_semantic_version("2.0.0"), parse_semantic_version("1.0.0"))
        self.assertGreater(parse_semantic_version("v2.0.0"), parse_semantic_version("1.5.0"))
        self.assertGreater(parse_semantic_version("2.0.1"), parse_semantic_version("2.0.0"))
        self.assertLess(parse_semantic_version("1.0.0"), parse_semantic_version("2.0.0"))
        self.assertEqual(parse_semantic_version("2.0.0"), parse_semantic_version("v2.0.0"))

    def test_dependency_update_worker_auto_update_flow(self):
        """Verifies that when an update is available and auto_apply is True, update is executed."""
        worker = DependencyUpdateWorker(auto_apply=True)
        status_msgs = []
        worker.status_message.connect(status_msgs.append)

        # Mock an update scenario via git
        with patch("shutil.which", return_value="/bin/git"), \
             patch("os.path.isdir", return_value=True), \
             patch("subprocess.run") as mock_run:
            def side_effect(cmd, **kwargs):
                ret = MagicMock()
                ret.returncode = 0
                if "rev-list" in cmd:
                    ret.stdout = "2\n"  # 2 commits behind
                elif "pull" in cmd:
                    ret.stdout = "Updating 123..456\nFast-forward\n"
                    ret.stderr = ""
                else:
                    ret.stdout = "master\n"
                return ret

            mock_run.side_effect = side_effect
            audit_events = []
            worker.audit_finished.connect(audit_events.append)
            worker.run()

            self.assertEqual(len(audit_events), 1)
            self.assertTrue(audit_events[0]["syncframe"]["updated"])
            self.assertTrue(any("SyncFrame atualizado com sucesso" in m for m in status_msgs))

    def test_lipsync_controller_contract(self):
        """Verifies LipSyncController signals, state transitions, and process handling."""
        ctrl = LipSyncController()
        self.assertTrue(hasattr(ctrl, "playback_state_changed"))
        self.assertTrue(hasattr(ctrl, "timecode_updated"))
        self.assertTrue(hasattr(ctrl, "status_changed"))

        states_recorded = []
        timecodes_recorded = []
        ctrl.playback_state_changed.connect(states_recorded.append)
        ctrl.timecode_updated.connect(timecodes_recorded.append)

        # Non-existent video returns False
        success = ctrl.play_marker(5, 0.0)
        self.assertFalse(success)

        # Set valid existing file
        test_file = "/bin/bash"
        ctrl.set_media(video_path=test_file, audio_path=test_file, duration_sec=100.0)

        # Mock QProcess to verify deterministic invocation without popping GUI window
        with patch.object(QProcess, "start") as mock_start:
            success = ctrl.play_marker(50, 150.0)
            self.assertTrue(success)
            self.assertTrue(mock_start.called)
            args_called = mock_start.call_args[0]
            prog = args_called[0]
            cmd_args = args_called[1]
            self.assertIn(prog, ["mpv", "ffplay"])
            self.assertTrue(any("--start=50.00" in a for a in cmd_args) or any("50.00" in a for a in cmd_args))
            self.assertIn(True, states_recorded)
            self.assertIn("00:00:50.000", timecodes_recorded)

        # Stop playback cleans up state
        ctrl.stop_playback()
        self.assertEqual(states_recorded[-1], False)

    def test_preview_player_integration(self):
        """Verifies PreviewPlayer integration with LipSyncController."""
        player = PreviewPlayer()
        self.assertFalse(player.btn_stop.isEnabled())
        self.assertEqual(player.btn_p05.text(), "5% · Abertura")
        self.assertEqual(player.btn_p50.text(), "50% · Meio")
        self.assertEqual(player.btn_p90.text(), "90% · Ato final")

        # Emitting controller playback state updates btn_stop
        player.controller.playback_state_changed.emit(True)
        self.assertTrue(player.btn_stop.isEnabled())

        player.controller.playback_state_changed.emit(False)
        self.assertFalse(player.btn_stop.isEnabled())

        player.close()

    def test_main_window_update_button_and_actions(self):
        """Verifies topbar includes btn_check_updates and check_for_updates method."""
        win = SyncFrameMainWindow()
        self.assertTrue(hasattr(win, "btn_check_updates"))
        self.assertEqual(win.btn_check_updates.text(), "Verificar Atualizações")
        self.assertFalse(win.btn_check_updates.isHidden())
        self.assertTrue(hasattr(win, "check_for_updates"))
        self.assertTrue(callable(win.check_for_updates))
        win.close()


if __name__ == "__main__":
    unittest.main()
