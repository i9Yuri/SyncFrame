"""Asynchronous QThread worker for single media container and audio inspection."""

import logging
from typing import Optional
from PySide6.QtCore import QThread, Signal

from ...core.inspector import inspect_single_media
from ...core.models import MediaInspectionReport

logger = logging.getLogger(__name__)


class SingleFileInspectionWorker(QThread):
    """
    Executes deep ffprobe media inspection in a background worker thread,
    preventing GUI thread freezes during container, audio, and video stream analysis.
    """
    inspection_completed = Signal(object)  # MediaInspectionReport
    inspection_failed = Signal(str)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        logger.info("Starting single file media inspection for %s", self.file_path)
        try:
            report = inspect_single_media(self.file_path)
            if self._is_cancelled:
                logger.info("Inspection cancelled for %s", self.file_path)
                return
            if report.error_message:
                self.inspection_failed.emit(report.error_message)
            else:
                self.inspection_completed.emit(report)
        except Exception as exc:
            if isinstance(exc, FileNotFoundError):
                logger.warning("Media file not found for inspection: %s", self.file_path)
            else:
                logger.error("Unhandled error inspecting %s: %s", self.file_path, exc, exc_info=True)
            if not self._is_cancelled:
                self.inspection_failed.emit(str(exc))
