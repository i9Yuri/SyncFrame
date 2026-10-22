"""Background QThread worker for executing lossless remux."""

import logging
import threading
import traceback
from typing import Optional

from PySide6.QtCore import QThread, Signal

from ...core.models import RemuxJob
from ...core.remuxer import execute_lossless_remux

logger = logging.getLogger(__name__)


class RemuxWorker(QThread):
    """
    Asynchronously executes mkvmerge remux with cancellation support and real-time progress.
    """
    progress = Signal(float, str)
    completed = Signal(bool, str)
    error = Signal(str)

    def __init__(self, job: RemuxJob):
        super().__init__()
        self.job = job
        self.cancel_event = threading.Event()

    def cancel(self):
        """Signals cancellation to terminate mkvmerge immediately."""
        self.cancel_event.set()

    def run(self):
        try:
            def on_progress(pct: float, log_line: str):
                self.progress.emit(pct, log_line)

            success = execute_lossless_remux(
                job=self.job,
                on_progress=on_progress,
                cancel_event=self.cancel_event
            )

            if success:
                self.completed.emit(True, f"Arquivo gerado com sucesso em:\n{self.job.output_path}")
            else:
                self.completed.emit(False, "Operação de remux cancelada pelo usuário.")

        except Exception as exc:
            logger.error("RemuxWorker failed: %s\n%s", exc, traceback.format_exc())
            self.error.emit(str(exc))
