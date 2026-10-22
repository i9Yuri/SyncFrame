"""Unit tests for temporary workspace lifecycle management."""

import os
import unittest
from src.core.temp_manager import TempWorkspace


class TestTempManager(unittest.TestCase):

    def test_workspace_creation_and_cleanup(self):
        ws = TempWorkspace(session_name="test_session_unit")
        staging_dir = ws.path
        self.assertTrue(os.path.isdir(staging_dir))

        # Create dummy intermediate WAV/PCM file
        dummy_file = ws.get_path("sample.wav")
        with open(dummy_file, "w") as f:
            f.write("DUMMY_PCM_DATA")
        self.assertTrue(os.path.isfile(dummy_file))

        # Clean up
        ws.cleanup()
        self.assertFalse(os.path.exists(staging_dir))
        self.assertFalse(os.path.exists(dummy_file))

    def test_workspace_context_manager(self):
        saved_path = None
        with TempWorkspace(session_name="test_context_unit") as ws:
            saved_path = ws.path
            self.assertTrue(os.path.exists(saved_path))
            temp_file = ws.get_path("scratch.tmp")
            with open(temp_file, "w") as f:
                f.write("content")
            self.assertTrue(os.path.exists(temp_file))

        # After exiting context, path should be gone
        self.assertFalse(os.path.exists(saved_path))


if __name__ == "__main__":
    unittest.main()
