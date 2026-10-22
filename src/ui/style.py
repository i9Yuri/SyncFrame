"""Neutral monochrome design system and stylesheet generator for SyncFrame."""

from typing import Literal

DARK_THEME_QSS = """
/* Global Window & Typography (Neutral Dark) */
QWidget {
    background-color: #121212;
    color: #e5e5e5;
    font-family: 'Inter', 'Cantarell', 'Segoe UI', system-ui, sans-serif;
    font-size: 13px;
    selection-background-color: #383838;
    selection-color: #ffffff;
}

QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* Cards & Surface Containers */
QFrame.bentoCard {
    background-color: #1a1a1a;
    border: 1px solid #2e2e2e;
    border-radius: 8px;
    padding: 12px;
}

QFrame.bentoCard:hover {
    border-color: #404040;
}

/* Headings & Metric Badges */
QLabel.cardTitle {
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: -0.2px;
}

QLabel.metricValue {
    color: #ffffff;
    font-family: 'JetBrains Mono', 'Fira Code', 'DejaVu Sans Mono', monospace;
    font-size: 20px;
    font-weight: 800;
}

QLabel.subText {
    color: #8c8c8c;
    font-size: 11px;
}

/* Status Badges (Strictly Utilitarian) */
QLabel.badgeGreen {
    background-color: rgba(34, 197, 94, 0.12);
    color: #4ade80;
    border: 1px solid rgba(34, 197, 94, 0.35);
    border-radius: 5px;
    padding: 2px 7px;
    font-weight: 600;
    font-size: 11px;
}

QLabel.badgeAmber {
    background-color: rgba(245, 158, 11, 0.12);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.35);
    border-radius: 5px;
    padding: 2px 7px;
    font-weight: 600;
    font-size: 11px;
}

QLabel.badgeNeutral {
    background-color: #242424;
    color: #d4d4d4;
    border: 1px solid #383838;
    border-radius: 5px;
    padding: 2px 7px;
    font-weight: 600;
    font-size: 11px;
}

/* Buttons */
QPushButton.btnPrimary {
    background-color: #2e2e2e;
    color: #ffffff;
    border: 1px solid #454545;
    border-radius: 6px;
    padding: 7px 15px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton.btnPrimary:hover {
    background-color: #3b3b3b;
    border-color: #555555;
}

QPushButton.btnPrimary:pressed {
    background-color: #222222;
}

QPushButton.btnPrimary:disabled {
    background-color: #1a1a1a;
    border-color: #2a2a2a;
    color: #555555;
}

QPushButton.btnSecondary {
    background-color: #202020;
    color: #cccccc;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 500;
}

QPushButton.btnSecondary:hover {
    background-color: #2b2b2b;
    border-color: #444444;
    color: #ffffff;
}

QPushButton.btnSecondary:pressed {
    background-color: #171717;
}

/* Primary Action / Remux Button (Utilitarian Emerald Accent) */
QPushButton.btnSuccess {
    background-color: #16a34a;
    color: #ffffff;
    border: 1px solid #22c55e;
    border-radius: 6px;
    padding: 9px 18px;
    font-weight: 700;
    font-size: 13px;
}

QPushButton.btnSuccess:hover {
    background-color: #15803d;
    border-color: #4ade80;
}

QPushButton.btnSuccess:disabled {
    background-color: #1e1e1e;
    border-color: #2e2e2e;
    color: #555555;
}

/* Abort Button */
QPushButton.btnDanger {
    background-color: rgba(220, 38, 38, 0.15);
    color: #f87171;
    border: 1px solid rgba(220, 38, 38, 0.35);
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
}

QPushButton.btnDanger:hover {
    background-color: #dc2626;
    color: #ffffff;
}

/* Inputs, Dropdowns & Spinboxes */
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #0d0d0d;
    color: #f5f5f5;
    border: 1px solid #2e2e2e;
    border-radius: 6px;
    padding: 6px 9px;
    font-family: 'JetBrains Mono', 'Fira Code', 'DejaVu Sans Mono', monospace;
    font-size: 12px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #666666;
}

QComboBox {
    background-color: #141414;
    color: #f0f0f0;
    border: 1px solid #2e2e2e;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #444444;
}

QComboBox:focus {
    border-color: #666666;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox QAbstractItemView {
    background-color: #1a1a1a;
    border: 1px solid #333333;
    color: #f0f0f0;
    selection-background-color: #2e2e2e;
    selection-color: #ffffff;
    padding: 4px;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 5px;
    background: #252525;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #666666;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #e5e5e5;
    border: 1px solid #999999;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #ffffff;
}

/* Progress Bar */
QProgressBar {
    background-color: #0d0d0d;
    border: 1px solid #2a2a2a;
    border-radius: 5px;
    height: 14px;
    text-align: center;
    color: #e5e5e5;
    font-size: 11px;
    font-weight: 600;
}

QProgressBar::chunk {
    background-color: #22c55e;
    border-radius: 4px;
}

/* Checkboxes & High-Contrast Toggles */
QCheckBox {
    color: #e5e5e5;
    font-size: 12px;
    font-weight: 500;
    spacing: 9px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    background-color: #181818;
    border: 1px solid #444444;
    border-radius: 4px;
}

QCheckBox::indicator:hover {
    border-color: #737373;
    background-color: #222222;
}

QCheckBox::indicator:checked {
    background-color: #10b981;
    border: 1px solid #059669;
    border-radius: 4px;
    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round'><polyline points='20 6 9 17 4 12'></polyline></svg>");
}

QCheckBox::indicator:checked:hover {
    background-color: #059669;
    border-color: #047857;
}

/* Collapsible Drawer & Secondary Containers */
QFrame#collapsibleSection {
    background-color: #161616;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
}

QPushButton.collapsibleBtn {
    background-color: transparent;
    color: #d4d4d4;
    border: none;
    text-align: left;
    font-size: 13px;
    font-weight: 700;
    padding: 2px 0px;
}

QPushButton.collapsibleBtn:hover {
    color: #ffffff;
}

/* Drop Frames, Summary Strips & Audit Cards */
QFrame.dropFrame {
    border: 2px dashed #383838;
    border-radius: 8px;
    background-color: #141414;
    padding: 20px;
}

QFrame.dropFrame:hover {
    border-color: #555555;
    background-color: #191919;
}

QFrame.summaryStrip {
    background-color: #121212;
    border: 1px solid #282828;
    border-radius: 6px;
    padding: 6px 10px;
}

QFrame.auditCard {
    background-color: #141414;
    border: 1px solid #262626;
    border-radius: 6px;
    padding: 8px 12px;
}

/* Terminal Log Area */
QPlainTextEdit, QTextEdit {
    background-color: #0d0d0d;
    color: #a3a3a3;
    border: 1px solid #242424;
    border-radius: 6px;
    font-family: 'JetBrains Mono', 'Fira Code', 'DejaVu Sans Mono', monospace;
    font-size: 11px;
    padding: 8px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #121212;
    width: 7px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #2e2e2e;
    min-height: 24px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #444444;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: #121212;
    height: 7px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #2e2e2e;
    min-width: 24px;
    border-radius: 3px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""

LIGHT_THEME_QSS = """
/* Global Window & Typography (Neutral Light) */
QWidget {
    background-color: #f4f4f5;
    color: #18181b;
    font-family: 'Inter', 'Cantarell', 'Segoe UI', system-ui, sans-serif;
    font-size: 13px;
    selection-background-color: #e4e4e7;
    selection-color: #09090b;
}

QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* Cards & Surface Containers */
QFrame.bentoCard {
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 8px;
    padding: 12px;
}

QFrame.bentoCard:hover {
    border-color: #d4d4d8;
}

/* Headings & Metric Badges */
QLabel.cardTitle {
    color: #09090b;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: -0.2px;
}

QLabel.metricValue {
    color: #09090b;
    font-family: 'JetBrains Mono', 'Fira Code', 'DejaVu Sans Mono', monospace;
    font-size: 20px;
    font-weight: 800;
}

QLabel.subText {
    color: #71717a;
    font-size: 11px;
}

/* Status Badges */
QLabel.badgeGreen {
    background-color: rgba(34, 197, 94, 0.12);
    color: #15803d;
    border: 1px solid rgba(34, 197, 94, 0.35);
    border-radius: 5px;
    padding: 2px 7px;
    font-weight: 600;
    font-size: 11px;
}

QLabel.badgeAmber {
    background-color: rgba(245, 158, 11, 0.12);
    color: #b45309;
    border: 1px solid rgba(245, 158, 11, 0.35);
    border-radius: 5px;
    padding: 2px 7px;
    font-weight: 600;
    font-size: 11px;
}

QLabel.badgeNeutral {
    background-color: #f4f4f5;
    color: #3f3f46;
    border: 1px solid #e4e4e7;
    border-radius: 5px;
    padding: 2px 7px;
    font-weight: 600;
    font-size: 11px;
}

/* Buttons */
QPushButton.btnPrimary {
    background-color: #18181b;
    color: #fafafa;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 7px 15px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton.btnPrimary:hover {
    background-color: #27272a;
    border-color: #3f3f46;
}

QPushButton.btnPrimary:pressed {
    background-color: #09090b;
}

QPushButton.btnPrimary:disabled {
    background-color: #e4e4e7;
    border-color: #d4d4d8;
    color: #a1a1aa;
}

QPushButton.btnSecondary {
    background-color: #ffffff;
    color: #27272a;
    border: 1px solid #d4d4d8;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 500;
}

QPushButton.btnSecondary:hover {
    background-color: #f4f4f5;
    border-color: #a1a1aa;
    color: #09090b;
}

/* Primary Action / Remux Button */
QPushButton.btnSuccess {
    background-color: #16a34a;
    color: #ffffff;
    border: 1px solid #15803d;
    border-radius: 6px;
    padding: 9px 18px;
    font-weight: 700;
    font-size: 13px;
}

QPushButton.btnSuccess:hover {
    background-color: #15803d;
    border-color: #166534;
}

QPushButton.btnSuccess:disabled {
    background-color: #e4e4e7;
    border-color: #d4d4d8;
    color: #a1a1aa;
}

/* Abort Button */
QPushButton.btnDanger {
    background-color: rgba(220, 38, 38, 0.1);
    color: #b91c1c;
    border: 1px solid rgba(220, 38, 38, 0.3);
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
}

QPushButton.btnDanger:hover {
    background-color: #dc2626;
    color: #ffffff;
}

/* Inputs, Dropdowns & Spinboxes */
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    color: #09090b;
    border: 1px solid #d4d4d8;
    border-radius: 6px;
    padding: 6px 9px;
    font-family: 'JetBrains Mono', 'Fira Code', 'DejaVu Sans Mono', monospace;
    font-size: 12px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #71717a;
}

QComboBox {
    background-color: #ffffff;
    color: #09090b;
    border: 1px solid #d4d4d8;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #a1a1aa;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #d4d4d8;
    color: #09090b;
    selection-background-color: #f4f4f5;
    selection-color: #09090b;
    padding: 4px;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 5px;
    background: #e4e4e7;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #71717a;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #18181b;
    border: 1px solid #27272a;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

/* Progress Bar */
QProgressBar {
    background-color: #e4e4e7;
    border: 1px solid #d4d4d8;
    border-radius: 5px;
    height: 14px;
    text-align: center;
    color: #18181b;
    font-size: 11px;
    font-weight: 600;
}

QProgressBar::chunk {
    background-color: #16a34a;
    border-radius: 4px;
}

/* Checkboxes & High-Contrast Toggles */
QCheckBox {
    color: #18181b;
    font-size: 12px;
    font-weight: 500;
    spacing: 9px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    background-color: #ffffff;
    border: 1px solid #9ca3af;
    border-radius: 4px;
}

QCheckBox::indicator:hover {
    border-color: #4b5563;
    background-color: #f9fafb;
}

QCheckBox::indicator:checked {
    background-color: #059669;
    border: 1px solid #047857;
    border-radius: 4px;
    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round'><polyline points='20 6 9 17 4 12'></polyline></svg>");
}

QCheckBox::indicator:checked:hover {
    background-color: #047857;
    border-color: #065f46;
}

/* Collapsible Drawer & Secondary Containers */
QFrame#collapsibleSection {
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 8px;
}

QPushButton.collapsibleBtn {
    background-color: transparent;
    color: #27272a;
    border: none;
    text-align: left;
    font-size: 13px;
    font-weight: 700;
    padding: 2px 0px;
}

QPushButton.collapsibleBtn:hover {
    color: #09090b;
}

/* Drop Frames, Summary Strips & Audit Cards */
QFrame.dropFrame {
    border: 2px dashed #d4d4d8;
    border-radius: 8px;
    background-color: #ffffff;
    padding: 20px;
}

QFrame.dropFrame:hover {
    border-color: #a1a1aa;
    background-color: #f8fafc;
}

QFrame.summaryStrip {
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 6px;
    padding: 6px 10px;
}

QFrame.auditCard {
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 6px;
    padding: 8px 12px;
}

/* Terminal Log Area */
QPlainTextEdit, QTextEdit {
    background-color: #ffffff;
    color: #3f3f46;
    border: 1px solid #e4e4e7;
    border-radius: 6px;
    font-family: 'JetBrains Mono', 'Fira Code', 'DejaVu Sans Mono', monospace;
    font-size: 11px;
    padding: 8px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #f4f4f5;
    width: 7px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #d4d4d8;
    min-height: 24px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #a1a1aa;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


def get_theme_qss(mode: Literal["dark", "light"] = "dark") -> str:
    """Returns the QSS stylesheet for the requested neutral theme."""
    return DARK_THEME_QSS if mode == "dark" else LIGHT_THEME_QSS


def apply_theme(target_widget, mode: Literal["dark", "light"] = "dark"):
    """Applies the neutral monochrome theme to the target application or widget."""
    target_widget.setStyleSheet(get_theme_qss(mode))
