"""Comprehensive unit and integration tests for Single-File Media Inspector and Dual-Mode Architecture."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtWidgets import QApplication

from src.core.models import (
    MediaInspectionReport,
    VideoStreamDetail,
    AudioStreamDetail,
    SubtitleDetail,
    ConsolidatedStreamSelection,
    RemuxJob,
    AutoMatchVerdict,
    StreamCandidate,
    StreamMetadata
)
from src.core.inspector import (
    inspect_single_media,
    build_consolidated_selection_state,
    apply_selection_to_remux_job
)
from src.core.remuxer import build_mkvmerge_hybrid_command
from src.ui.components.media_inspector_view import MediaInspectorView, get_resolution_label, format_duration
from src.ui.components.unified_drop_zone import UnifiedDropZone
from src.ui.main_window import SyncFrameMainWindow

app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)


def make_stream_candidate(
    stream_id: int,
    track_type: str,
    codec: str,
    language: str = "und",
    channels: int = 2,
    file_path: str = "/movies/sample.mkv",
    fps: float = 23.976,
    width: int = 1920,
    height: int = 1080,
    title: str = ""
) -> StreamCandidate:
    meta = StreamMetadata(
        id=stream_id,
        codec=codec,
        channels=channels,
        sample_rate=48000,
        fps=fps,
        duration_ms=60000.0,
        language=language,
        is_default=False,
        track_type=track_type,
        width=width,
        height=height,
        title=title,
        container_format="mkv"
    )
    return StreamCandidate(stream=meta, file_path=file_path)


class TestMediaInspectorCore(unittest.TestCase):
    """Tests inspect_single_media probing and fallback handling."""

    @patch("subprocess.run")
    @patch("os.path.isfile", return_value=True)
    @patch("os.path.getsize", return_value=4_500_000_000)
    def test_inspect_single_media_video_container(self, mock_size, mock_isfile, mock_run):
        ffprobe_mock = {
            "format": {
                "format_name": "matroska,webm",
                "duration": "7200.5"
            },
            "streams": [
                {
                    "index": 0,
                    "codec_type": "video",
                    "codec_name": "hevc",
                    "profile": "Main 10",
                    "width": 3840,
                    "height": 2160,
                    "display_aspect_ratio": "16:9",
                    "r_frame_rate": "24000/1001",
                    "bits_per_raw_sample": "10",
                    "color_space": "bt2020nc",
                    "color_transfer": "smpte2084",
                    "side_data_list": [{"side_data_type": "DOVI configuration record"}]
                },
                {
                    "index": 1,
                    "codec_type": "audio",
                    "codec_name": "truehd",
                    "channels": 8,
                    "channel_layout": "7.1",
                    "sample_rate": "48000",
                    "bit_rate": "4500000",
                    "tags": {"language": "por", "title": "Dublagem Dolby Atmos"}
                },
                {
                    "index": 2,
                    "codec_type": "subtitle",
                    "codec_name": "subrip",
                    "tags": {"language": "por", "title": "Português Completa"},
                    "disposition": {"default": 1, "forced": 0}
                }
            ],
            "chapters": [{"id": 0}, {"id": 1}, {"id": 2}]
        }
        mock_run.return_value = MagicMock(stdout=import_json_dumps(ffprobe_mock), stderr="", returncode=0)

        report = inspect_single_media("/movies/movie_4k.mkv")
        self.assertEqual(report.file_name, "movie_4k.mkv")
        self.assertEqual(report.container_format, "MKV")
        self.assertFalse(report.is_audio_only)
        self.assertEqual(len(report.video_streams), 1)
        self.assertEqual(len(report.audio_streams), 1)
        self.assertEqual(len(report.subtitle_streams), 1)
        self.assertEqual(report.chapter_count, 3)

        v0 = report.video_streams[0]
        self.assertEqual(v0.width, 3840)
        self.assertEqual(v0.height, 2160)
        self.assertEqual(v0.bit_depth, 10)
        self.assertIn("Dolby Vision", v0.hdr_format)

        a0 = report.audio_streams[0]
        self.assertEqual(a0.codec, "truehd")
        self.assertEqual(a0.channels, 8)
        self.assertEqual(a0.language, "por")

    @patch("subprocess.run")
    @patch("os.path.isfile", return_value=True)
    @patch("os.path.getsize", return_value=350_000_000)
    def test_inspect_single_media_isolated_audio(self, mock_size, mock_isfile, mock_run):
        ffprobe_mock = {
            "format": {
                "format_name": "flac",
                "duration": "3600.0"
            },
            "streams": [
                {
                    "index": 0,
                    "codec_type": "audio",
                    "codec_name": "flac",
                    "channels": 6,
                    "channel_layout": "5.1(side)",
                    "sample_rate": "48000",
                    "tags": {"language": "por", "title": "Dublagem 5.1"}
                }
            ],
            "chapters": []
        }
        mock_run.return_value = MagicMock(stdout=import_json_dumps(ffprobe_mock), stderr="", returncode=0)

        report = inspect_single_media("/audios/dubbed.flac")
        self.assertEqual(report.file_name, "dubbed.flac")
        self.assertTrue(report.is_audio_only)
        self.assertEqual(len(report.video_streams), 0)
        self.assertEqual(len(report.audio_streams), 1)
        self.assertEqual(report.audio_streams[0].codec, "flac")
        self.assertEqual(report.audio_streams[0].channels, 6)

    @patch("subprocess.run", side_effect=Exception("Corrupted container header"))
    @patch("os.path.isfile", return_value=True)
    @patch("os.path.getsize", return_value=1024)
    def test_inspect_single_media_corrupted_fallback(self, mock_size, mock_isfile, mock_run):
        report = inspect_single_media("/corrupt/truncated.mkv")
        self.assertIsNotNone(report.error_message)
        self.assertIn("Falha ao inspecionar", report.error_message)


class TestConsolidatedStreamSelection(unittest.TestCase):
    """Tests consolidated stream selection and RemuxJob integration."""

    def setUp(self):
        self.v_cand = make_stream_candidate(0, "video", "hevc", file_path="/movies/source_video.mkv")
        self.t_cand = make_stream_candidate(1, "audio", "eac3", language="por", channels=6, file_path="/movies/source_audio.mkv")
        self.r_cand = make_stream_candidate(1, "audio", "truehd", language="eng", channels=8, file_path="/movies/source_video.mkv")
        self.extra_cand = make_stream_candidate(2, "audio", "ac3", language="spa", channels=2, file_path="/movies/source_video.mkv")

        self.verdict = AutoMatchVerdict(
            recommended_video=self.v_cand,
            alternative_videos=[],
            recommended_target_audio=self.t_cand,
            alternative_audios=[self.extra_cand],
            reference_audio=self.r_cand
        )

    def test_build_consolidated_selection_state(self):
        sel = build_consolidated_selection_state(["/movies/source_video.mkv", "/movies/source_audio.mkv"], self.verdict)
        self.assertEqual(sel.primary_video_file, "/movies/source_video.mkv")
        self.assertEqual(sel.primary_video_track_id, 0)
        self.assertEqual(sel.target_audio_file, "/movies/source_audio.mkv")
        self.assertEqual(sel.target_audio_track_id, 1)

        # English reference audio should be checked by default
        eng_selected = False
        for fp, tid, is_checked in sel.secondary_audio_selections:
            if fp == "/movies/source_video.mkv" and tid == 1:
                eng_selected = is_checked
        self.assertTrue(eng_selected, "English original audio should default to checked")

    def test_apply_selection_to_remux_job(self):
        sel = build_consolidated_selection_state(["/movies/source_video.mkv", "/movies/source_audio.mkv"], self.verdict)
        base_job = RemuxJob(
            output_path="/out/final.mkv",
            video_file="",
            target_audio_file="",
            offset_ms=-120.0,
            stretch_ratio=1.0,
            keep_original_audio=False
        )

        job = apply_selection_to_remux_job(sel, base_job)
        self.assertEqual(job.video_file, "/movies/source_video.mkv")
        self.assertEqual(job.target_audio_file, "/movies/source_audio.mkv")
        self.assertTrue(job.keep_original_audio)
        self.assertEqual(len(job.secondary_audio_selections), len(sel.secondary_audio_selections))

    def test_build_mkvmerge_hybrid_command_with_secondary_selections(self):
        secondary = [
            ("/movies/source_video.mkv", 1, True),   # English audio kept
            ("/movies/source_video.mkv", 2, False),  # Spanish audio omitted
        ]
        cmd = build_mkvmerge_hybrid_command(
            video_mkv="/movies/source_video.mkv",
            audio_source="/movies/source_audio.mkv",
            offset_ms=-150.0,
            output_path="/out/final.mkv",
            video_track_id=0,
            target_audio_track_id=1,
            secondary_audio_selections=secondary
        )
        cmd_str = " ".join(cmd)
        self.assertIn("--audio-tracks 1", cmd_str)
        self.assertIn("--sync 1:", cmd_str)
        self.assertIn("--default-track-flag 1:yes", cmd_str)


class TestMediaInspectorViewUI(unittest.TestCase):
    """Tests visual inspection component formatting and rounded geometry."""

    def test_helpers(self):
        self.assertEqual(get_resolution_label(3840, 2160), "3840x2160 (4K UHD)")
        self.assertEqual(get_resolution_label(1920, 1080), "1920x1080 (Full HD 1080p)")
        self.assertEqual(format_duration(3665), "01:01:05")

    def test_media_inspector_view_rendering(self):
        view = MediaInspectorView()
        report = MediaInspectionReport(
            file_path="/movies/demo.mkv",
            file_name="demo.mkv",
            file_size_bytes=2_000_000_000,
            duration_sec=5400.0,
            container_format="MKV",
            video_streams=[
                VideoStreamDetail(
                    stream_id=0,
                    codec="hevc",
                    profile="Main 10",
                    width=3840,
                    height=2160,
                    aspect_ratio="16:9",
                    fps=23.976,
                    bit_depth=10,
                    color_space="bt2020nc",
                    hdr_format="HDR10"
                )
            ],
            audio_streams=[
                AudioStreamDetail(
                    stream_id=1,
                    language="por",
                    title="Dublagem 5.1",
                    codec="eac3",
                    channels=6,
                    channel_layout="5.1",
                    sample_rate=48000,
                    bit_rate=640000,
                    is_immersive=False
                )
            ],
            subtitle_streams=[
                SubtitleDetail(stream_id=2, language="por", title="Forçada", codec="subrip", is_forced=True)
            ],
            chapter_count=12,
            is_audio_only=False
        )

        view.set_report(report)
        self.assertTrue(view.card_loading.isHidden())
        self.assertTrue(view.card_error.isHidden())
        self.assertFalse(view.report_container.isHidden())
        view.deleteLater()


class TestDualModeDropZoneAndWorkbench(unittest.TestCase):
    """Tests dual mode state machine in UnifiedDropZone and MainWindow."""

    def setUp(self):
        self.dz = UnifiedDropZone()

    def tearDown(self):
        if hasattr(self.dz, "_worker") and self.dz._worker and self.dz._worker.isRunning():
            self.dz._worker.wait(500)
        self.dz.deleteLater()

    @patch("src.ui.components.unified_drop_zone.SingleFileInspectionWorker")
    def test_single_file_ingestion_switches_to_inspector(self, mock_worker_cls):
        mock_worker = MagicMock()
        mock_worker_cls.return_value = mock_worker

        self.assertEqual(self.dz.stack.currentIndex(), 0)

        # Simulate 1 file dropped
        self.dz.handle_files_ingested(["/movies/test_single_video.mkv"])
        self.assertEqual(len(self.dz.loaded_files), 1)
        self.assertEqual(self.dz.stack.currentIndex(), 1)
        self.assertIn("test_single_video.mkv", self.dz.lbl_single_filename.text())
        mock_worker.start.assert_called_once()

    def test_second_file_transition_to_sync_mode(self):
        ready_files = []
        self.dz.files_ready.connect(lambda a, b: ready_files.append((a, b)))

        with patch("src.ui.components.unified_drop_zone.SingleFileInspectionWorker"):
            self.dz.handle_files_ingested(["/movies/test_video.mkv"])
            self.assertEqual(self.dz.stack.currentIndex(), 1)

            # Add second file
            self.dz.handle_files_ingested(["/movies/test_audio.m4a"])
            self.assertEqual(len(self.dz.loaded_files), 2)
            self.assertEqual(len(ready_files), 1)
            self.assertEqual(ready_files[0], ("/movies/test_video.mkv", "/movies/test_audio.m4a"))

    def test_review_gate_has_secondary_audio_section(self):
        self.assertTrue(hasattr(self.dz, "frame_secondary_audio"))
        self.assertTrue(hasattr(self.dz, "secondary_layout"))
        self.assertEqual(self.dz.chip_fsa_status.height(), 24)

    def test_consolidated_selection_contract(self):
        sel = self.dz.get_consolidated_selection()
        self.assertIsInstance(sel, ConsolidatedStreamSelection)

    @patch("src.ui.main_window.SyncFrameMainWindow.check_for_updates")
    def test_main_window_transitions(self, mock_updates):
        win = SyncFrameMainWindow()
        try:
            report = MediaInspectionReport(
                file_path="/movies/test.mkv",
                file_name="test.mkv",
                file_size_bytes=1000,
                duration_sec=100.0,
                container_format="MKV",
                video_streams=[],
                audio_streams=[],
                subtitle_streams=[],
                chapter_count=0,
                is_audio_only=False
            )
            win.transition_to_inspector_mode(report)
            self.assertFalse(win.card_remux_exec.isEnabled())
            self.assertFalse(win.card_acoustic.isEnabled())
            self.assertFalse(win.sync_controls.isEnabled())
            self.assertFalse(win.preview_player.isEnabled())

            v_cand = make_stream_candidate(0, "video", "hevc", file_path="/movies/v.mkv")
            a_cand = make_stream_candidate(1, "audio", "eac3", language="por", channels=6, file_path="/movies/a.mkv")
            with patch("src.ui.main_window.evaluate_media_streams") as mock_eval:
                mock_eval.return_value = AutoMatchVerdict(
                    recommended_video=v_cand,
                    alternative_videos=[],
                    recommended_target_audio=a_cand,
                    alternative_audios=[],
                    reference_audio=None
                )
                win.transition_to_sync_mode(["/movies/v.mkv", "/movies/a.mkv"])
                self.assertTrue(win.card_remux_exec.isEnabled())
                self.assertTrue(win.card_acoustic.isEnabled())
                self.assertTrue(win.sync_controls.isEnabled())
                self.assertTrue(win.preview_player.isEnabled())
        finally:
            win.close()
            win.deleteLater()


def import_json_dumps(obj):
    import json
    return json.dumps(obj)


if __name__ == "__main__":
    unittest.main()
