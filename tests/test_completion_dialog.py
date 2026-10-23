"""Unit tests for CompletionDialog and runtime resource resolution."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication

from src.ui.components.completion_dialog import (
    CompletionDialog,
    get_runtime_resource_path,
    open_containing_folder,
    show_completion_modal
)

app = QApplication.instance()
if not app:
    app = QApplication([])


class TestCompletionDialog(unittest.TestCase):

    def test_dialog_instantiation_and_widgets(self):
        sample_path = "/movies/film_4k_synced.mkv"
        dialog = CompletionDialog(output_file_path=sample_path)

        self.assertEqual(dialog.output_file_path, sample_path)
        self.assertEqual(dialog.txt_path.text(), sample_path)
        self.assertTrue(dialog.txt_path.isReadOnly())
        self.assertEqual(dialog.glyph_badge.text(), "✓")
        self.assertEqual(dialog.windowTitle(), "Processo Concluído — SyncFrame")
        self.assertTrue(dialog.btn_close.isDefault())

    def test_get_runtime_resource_path_dev_mode(self):
        # In normal execution (no sys._MEIPASS)
        path = get_runtime_resource_path("src/ui/style.py")
        self.assertTrue(os.path.isabs(path))
        self.assertTrue(path.endswith("src/ui/style.py"))

    def test_get_runtime_resource_path_meipass_mode(self):
        # Simulate PyInstaller bundled mode with _MEIPASS
        fake_meipass = "/tmp/fake_meipass_123"
        with patch.object(sys, "_MEIPASS", fake_meipass, create=True):
            path = get_runtime_resource_path("icon.png")
            self.assertEqual(path, "/tmp/fake_meipass_123/icon.png")

    @patch("shutil.which")
    @patch("subprocess.Popen")
    def test_open_containing_folder_dolphin(self, mock_popen, mock_which):
        def fake_which(cmd):
            return "/usr/bin/dolphin" if cmd == "dolphin" else None

        mock_which.side_effect = fake_which

        with patch("os.path.exists", return_value=True), patch("os.path.isfile", return_value=True):
            result = open_containing_folder("/home/user/video_synced.mkv")
            self.assertTrue(result)
            mock_popen.assert_called_once()
            args = mock_popen.call_args[0][0]
            self.assertEqual(args[0], "dolphin")
            self.assertIn("--select", args)

    @patch("shutil.which")
    @patch("subprocess.Popen")
    def test_open_containing_folder_nautilus(self, mock_popen, mock_which):
        def fake_which(cmd):
            return "/usr/bin/nautilus" if cmd == "nautilus" else None

        mock_which.side_effect = fake_which

        with patch("os.path.exists", return_value=True), patch("os.path.isfile", return_value=True):
            result = open_containing_folder("/home/user/video_synced.mkv")
            self.assertTrue(result)
            mock_popen.assert_called_once()
            args = mock_popen.call_args[0][0]
            self.assertEqual(args[0], "nautilus")
            self.assertIn("--select", args)

    @patch("shutil.which")
    @patch("subprocess.Popen")
    def test_open_containing_folder_xdg_open(self, mock_popen, mock_which):
        def fake_which(cmd):
            return "/usr/bin/xdg-open" if cmd == "xdg-open" else None

        mock_which.side_effect = fake_which

        with patch("os.path.exists", return_value=True), patch("os.path.isfile", return_value=True):
            result = open_containing_folder("/home/user/video_synced.mkv")
            self.assertTrue(result)
            mock_popen.assert_called_once()
            args = mock_popen.call_args[0][0]
            self.assertEqual(args[0], "xdg-open")
            self.assertEqual(args[1], "/home/user")

    def test_open_containing_folder_empty(self):
        self.assertFalse(open_containing_folder(""))

    @patch("src.ui.components.completion_dialog.open_containing_folder")
    def test_button_open_folder_success(self, mock_open):
        mock_open.return_value = True
        dialog = CompletionDialog("/tmp/output.mkv")
        dialog._on_open_folder_clicked()
        self.assertIn("Aberta", dialog.btn_open_folder.text())

    @patch("src.ui.components.completion_dialog.open_containing_folder")
    def test_button_open_folder_fallback_clipboard(self, mock_open):
        mock_open.return_value = False
        dialog = CompletionDialog("/tmp/output_fallback.mkv")
        dialog._on_open_folder_clicked()
        self.assertIn("Caminho Copiado", dialog.btn_open_folder.text())
        self.assertEqual(QApplication.clipboard().text(), "/tmp/output_fallback.mkv")


if __name__ == "__main__":
    unittest.main()
