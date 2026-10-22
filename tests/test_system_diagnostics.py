"""Unit tests for system crash diagnostics and dependencies checking."""

import subprocess
import unittest
from unittest.mock import MagicMock, patch

from src.utils.system_check import (
    SystemDiagnostics,
    check_system_dependencies,
    diagnose_system_crash_logs
)


class TestSystemDiagnostics(unittest.TestCase):

    def test_system_diagnostics_dataclass(self):
        diag = SystemDiagnostics(
            ffmpeg_available=True,
            ffprobe_available=True,
            mkvmerge_available=True,
            missing_required=[]
        )
        self.assertTrue(diag.is_operational)

        diag_missing = SystemDiagnostics(
            ffmpeg_available=True,
            ffprobe_available=False,
            mkvmerge_available=True,
            missing_required=["ffprobe"]
        )
        self.assertFalse(diag_missing.is_operational)
        self.assertIn("sudo dnf install", diag_missing.install_instructions())

    @patch("shutil.which")
    def test_check_system_dependencies_all_present(self, mock_which):
        mock_which.side_effect = lambda tool: f"/usr/bin/{tool}"
        diag = check_system_dependencies()
        self.assertTrue(diag.is_operational)
        self.assertTrue(diag.ffmpeg_available)
        self.assertTrue(diag.mkvmerge_available)
        self.assertEqual(len(diag.missing_required), 0)

    @patch("subprocess.run")
    def test_diagnose_system_crash_logs_oom(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Oct 22 19:10:00 kernel: Out of memory: Killed process 1234 (python3) total-vm:32000000kB"
        )
        report = diagnose_system_crash_logs()
        self.assertEqual(report["oom_detected"], "True")
        self.assertIn("OOM", report["last_reboot_type"])
        self.assertIn("streaming estrito", report["recommended_mitigation"])

    @patch("subprocess.run")
    def test_diagnose_system_crash_logs_mce(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Oct 22 19:10:00 kernel: MCE: [Hardware Error]: Machine check events logged"
        )
        report = diagnose_system_crash_logs()
        self.assertEqual(report["mce_hardware_error"], "True")
        self.assertIn("Falha de Hardware", report["last_reboot_type"])

    @patch("subprocess.run")
    def test_diagnose_system_crash_logs_abrupt_ocp(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                "Oct 22 19:10:18 mkvmerge[4567]: Progress: 10%\n"
                "Oct 22 19:10:19 thermald[123]: Unsupported cpu model or deactivated\n"
            )
        )
        report = diagnose_system_crash_logs()
        self.assertEqual(report["oom_detected"], "False")
        self.assertEqual(report["mce_hardware_error"], "False")
        self.assertIn("Desarme Abrupto", report["last_reboot_type"])
        self.assertIn("-threads 2", report["recommended_mitigation"])
        self.assertIn("thermald inativo", report["thermal_status"])

    @patch("subprocess.run")
    def test_diagnose_system_crash_logs_clean_shutdown(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Oct 22 19:10:00 systemd[1]: Reached target Shutdown.\nOct 22 19:10:01 kernel: reboot: Restarting system"
        )
        report = diagnose_system_crash_logs()
        self.assertEqual(report["last_reboot_type"], "Desconhecido / Não diagnosticado")

    @patch("subprocess.run")
    def test_diagnose_system_crash_logs_unavailable(self, mock_run):
        mock_run.side_effect = FileNotFoundError("journalctl not found")
        report = diagnose_system_crash_logs()
        self.assertIn("inacessível", report["last_reboot_type"])


if __name__ == "__main__":
    unittest.main()
