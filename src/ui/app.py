"""Application instance factory and global styling configuration."""

import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from .style import DARK_THEME_QSS


def create_application() -> QApplication:
    """
    Instantiates and configures the PySide6 QApplication with Pro Max v4 styling.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setApplicationName("SyncFrame")
    app.setApplicationDisplayName("SyncFrame")
    app.setOrganizationName("i9Yuri")
    app.setApplicationVersion("1.0.0")

    # Apply stylesheet
    app.setStyleSheet(DARK_THEME_QSS)

    return app
