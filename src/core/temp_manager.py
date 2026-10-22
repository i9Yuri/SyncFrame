"""Temporary workspace manager with guaranteed lifecycle cleanup."""

import atexit
import logging
import os
import shutil
import signal
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

# Base temporary directory inside project or system fallback
DEFAULT_TMP_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".syncframe_tmp"))


class TempWorkspace:
    """
    Manages an isolated temporary staging directory for PCM audio, waveforms,
    and intermediate files. Automatically cleans up upon exit or abort.
    """
    _registered_workspaces = []
    _signals_registered = False

    def __init__(self, base_dir: Optional[str] = None, session_name: Optional[str] = None):
        self.base_dir = os.path.abspath(base_dir) if base_dir else DEFAULT_TMP_BASE
        session_id = session_name or f"session_{uuid.uuid4().hex[:8]}"
        self.path = os.path.join(self.base_dir, session_id)
        self._cleaned = False
        
        # Ensure directory exists
        os.makedirs(self.path, exist_ok=True)
        
        TempWorkspace._registered_workspaces.append(self)
        TempWorkspace._ensure_signal_handlers()

    @classmethod
    def _ensure_signal_handlers(cls):
        """Register atexit and signal handlers once to guarantee cleanup."""
        if cls._signals_registered:
            return
        cls._signals_registered = True
        atexit.register(cls.cleanup_all)
        
        def handle_signal(sig, frame):
            logger.info("Signal %s received. Performing emergency staging cleanup...", sig)
            cls.cleanup_all()
            # Restore default and re-raise
            signal.signal(sig, signal.SIG_DFL)
            os.kill(os.getpid(), sig)

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, handle_signal)
            except (ValueError, OSError):
                # Ignore if not in main thread
                pass

    @classmethod
    def cleanup_all(cls):
        """Clean up all registered temporary workspaces."""
        for ws in list(cls._registered_workspaces):
            ws.cleanup()

    def get_path(self, filename: str) -> str:
        """Returns the full absolute path for a file inside this staging workspace."""
        return os.path.join(self.path, filename)

    def cleanup(self):
        """Recursively removes this workspace directory and all contained files."""
        if self._cleaned:
            return
        self._cleaned = True
        if os.path.exists(self.path):
            try:
                shutil.rmtree(self.path, ignore_errors=True)
                logger.debug("Cleaned staging workspace: %s", self.path)
            except Exception as exc:
                logger.warning("Failed to remove staging workspace %s: %s", self.path, exc)
        
        if self in TempWorkspace._registered_workspaces:
            TempWorkspace._registered_workspaces.remove(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
