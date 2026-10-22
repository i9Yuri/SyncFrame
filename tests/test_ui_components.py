"""Unit tests for UI components: AudioPreserveCheckbox, CollapsibleSection, and UnifiedPipelineWorker."""

import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication, QLabel

from src.core.models import RemuxJob
from src.ui.components.audio_preserve_checkbox import AudioPreserveCheckbox
from src.ui.components.collapsible_section import CollapsibleSection
from src.ui.workers.unified_pipeline_worker import UnifiedPipelineWorker

app = QApplication.instance()
if not app:
    app = QApplication([])


class TestUIComponents(unittest.TestCase):

    def test_audio_preserve_checkbox_states_and_text(self):
        cb = AudioPreserveCheckbox(None, language_name="inglês")
        # Default is checked
        self.assertTrue(cb.isChecked())
        self.assertIn("Sim (Faixa Secundária)", cb.text())
        self.assertIn("inglês", cb.text())

        # Uncheck
        cb.setChecked(False)
        self.assertFalse(cb.isChecked())
        self.assertIn("Não", cb.text())
        self.assertNotIn("Faixa Secundária", cb.text())

        # Check again
        cb.setChecked(True)
        self.assertTrue(cb.isChecked())
        self.assertIn("Sim (Faixa Secundária)", cb.text())

        # Custom language update
        cb.set_language_name("japonês")
        self.assertIn("japonês", cb.text())
        cb.setChecked(False)
        self.assertIn("japonês", cb.text())
        self.assertIn("Não", cb.text())

    def test_collapsible_section_toggle(self):
        section = CollapsibleSection("Ajustes Avançados")
        dummy_content = QLabel("Advanced Content")
        section.set_content_widget(dummy_content)

        # Starts collapsed
        self.assertFalse(section.is_expanded)
        self.assertTrue(section.content_widget.isHidden())
        self.assertIn("▶", section.btn_toggle.text())

        # Toggle to expand
        section.toggle()
        self.assertTrue(section.is_expanded)
        self.assertFalse(section.content_widget.isHidden())
        self.assertIn("▼", section.btn_toggle.text())

        # Toggle to collapse
        section.toggle()
        self.assertFalse(section.is_expanded)
        self.assertTrue(section.content_widget.isHidden())
        self.assertIn("▶", section.btn_toggle.text())

    @patch("src.ui.workers.unified_pipeline_worker.execute_lossless_remux")
    @patch("src.ui.workers.unified_pipeline_worker.extract_reference_channel")
    @patch("src.ui.workers.unified_pipeline_worker.compute_acoustic_correlation")
    def test_unified_pipeline_worker_manual_offset(
        self, mock_correlate, mock_extract, mock_remux
    ):
        mock_remux.return_value = True
        job = RemuxJob(
            output_path="/tmp/out.mkv",
            video_file="/tmp/vid.mkv",
            target_audio_file="/tmp/aud.mkv",
            offset_ms=0.0,
            stretch_ratio=1.0,
            keep_original_audio=True
        )
        worker = UnifiedPipelineWorker(job, manual_offset_override=250.0)

        metrics_emitted = []
        completed_emitted = []

        worker.metrics_ready.connect(metrics_emitted.append)
        worker.completed.connect(lambda s, m: completed_emitted.append((s, m)))

        # Run synchronously for testing
        worker.run()

        # In manual offset mode, acoustic correlation and reference channel extraction are skipped
        mock_extract.assert_not_called()
        mock_correlate.assert_not_called()
        self.assertEqual(len(metrics_emitted), 0)
        self.assertEqual(job.offset_ms, 250.0)
        self.assertTrue(completed_emitted[0][0])
        mock_remux.assert_called_once()

    def test_unified_pipeline_worker_cancellation(self):
        job = RemuxJob(
            output_path="/tmp/out.mkv",
            video_file="/tmp/vid.mkv",
            target_audio_file="/tmp/aud.mkv",
            offset_ms=0.0,
            stretch_ratio=1.0,
            keep_original_audio=True
        )
        worker = UnifiedPipelineWorker(job)
        worker.cancel()

        completed_emitted = []
        worker.completed.connect(lambda s, m: completed_emitted.append((s, m)))

        worker.run()

        self.assertEqual(len(completed_emitted), 1)
        self.assertFalse(completed_emitted[0][0])
        self.assertIn("cancelad", completed_emitted[0][1].lower())


if __name__ == "__main__":
    unittest.main()
