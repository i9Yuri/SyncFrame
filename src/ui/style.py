import os
from typing import Dict, Literal, Optional
from PySide6.QtWidgets import QApplication

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
CHECK_GLYPH_PATH = os.path.join(ASSETS_DIR, "check_glyph.png")


def get_check_icon_path() -> str:
    """Returns the absolute file path to the checkmark glyph icon, generating it if needed."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    if not os.path.isfile(CHECK_GLYPH_PATH):
        try:
            from PySide6.QtGui import QImage, QPainter, QColor, QPen
            from PySide6.QtCore import Qt, QPoint
            img = QImage(18, 18, QImage.Format_ARGB32)
            img.fill(Qt.transparent)
            painter = QPainter(img)
            painter.setRenderHint(QPainter.Antialiasing, True)
            pen = QPen(QColor(16, 185, 129), 2.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(QPoint(3, 9), QPoint(7, 13))
            painter.drawLine(QPoint(7, 13), QPoint(14, 5))
            painter.end()
            img.save(CHECK_GLYPH_PATH)
        except Exception:
            pass
    return CHECK_GLYPH_PATH.replace("\\", "/")


def get_theme_tokens(mode: Literal["dark", "light"] = "dark") -> Dict[str, str]:
    """Returns the atomic color tokens for the specified monochrome theme."""
    if mode == "dark":
        return {
            "bg_base": "#000000",
            "bg_card": "#1b1c20",
            "bg_card_secondary": "#26272d",
            "bg_card_tertiary": "#33343b",
            "text_primary": "#f2f3f7",
            "text_secondary": "#9a9eac",
            "accent_active": "#ffffff",
            "accent_inactive": "#40424c",
            "border_subtle": "#2d2f36",
        }
    return {
        "bg_base": "#f1f2f6",
        "bg_card": "#ffffff",
        "bg_card_secondary": "#eceef4",
        "bg_card_tertiary": "#e1e4ed",
        "text_primary": "#16181d",
        "text_secondary": "#6a7080",
        "accent_active": "#16181d",
        "accent_inactive": "#dcdfe8",
        "border_subtle": "#dcdfe8",
    }


# ==============================================================================
# Dark Theme QSS (One UI Modern Card Ergonomics: #000000 base, #1b1c20 cards, #f2f3f7 text)
# Legacy compatibility tokens preserved: #0a0b0d, #111317, #eef0f2
# ==============================================================================
DARK_THEME_QSS = """
/* Global Window & Typography (One UI Precision Dark: #000000 base, #0a0b0d fallback) */
QWidget {
    background-color: #000000;
    color: #f2f3f7;
    font-family: 'Inter', 'Segoe UI', 'Liberation Sans', -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #33343b;
    selection-color: #f2f3f7;
}

/* Universal Label Reset: Eradicate hard opaque backgrounds and border artifacts */
QLabel {
    background-color: transparent;
    background: transparent;
    border: none;
}

QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* Workbench Topbar: Continuous clean surface */
QWidget#workbenchTopbar {
    background-color: #1b1c20;
    border-bottom: 1px solid #2d2f36;
}

QLabel#brandTitle {
    background-color: transparent;
    color: #f2f3f7;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: -0.4px;
    border: none;
}

QLabel#brandSubtitle {
    background-color: transparent;
    color: #9a9eac;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.2px;
    border: none;
}

QLabel#topCrumb {
    background-color: transparent;
    color: #9a9eac;
    font-size: 12px;
    border: none;
}

QLabel#topCrumb strong {
    color: #f2f3f7;
    font-weight: 600;
}

/* One UI Primary Bento/Panel Cards: Generous 28px rounded corners (#1b1c20, #111317 compat) */
QFrame.panelCard, QFrame.bentoCard {
    background-color: #1b1c20;
    border: 1px solid #2d2f36;
    border-radius: 28px;
}

/* Floating Bottom Dock: Seamless 34px rounded capsule container */
QFrame#floatingDock, QFrame.floatingDock, QFrame#eventLogDrawer {
    background-color: #1b1c20;
    border: 1px solid #2d2f36;
    border-radius: 34px;
}

/* Subcards / Inset Containers: 22px rounded corners */
QFrame.subCard {
    background-color: #26272d;
    border: 1px solid #2d2f36;
    border-radius: 22px;
}

/* Panel Header and Headings */
QLabel.sectionIndex {
    background-color: transparent;
    color: #9a9eac;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    border: none;
}

QLabel.cardTitle {
    background-color: transparent;
    color: #f2f3f7;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: -0.2px;
    border: none;
}

QLabel.subText {
    background-color: transparent;
    color: #9a9eac;
    font-size: 11px;
    border: none;
}

QLabel.dropTitle {
    background-color: transparent;
    color: #f2f3f7;
    font-size: 14px;
    font-weight: 700;
    border: none;
}

QLabel.logTitle {
    background-color: transparent;
    color: #f2f3f7;
    font-size: 12px;
    font-weight: 700;
    border: none;
}

QLabel.eyebrowText {
    background-color: transparent;
    color: #9a9eac;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.0px;
    border: none;
}

/* Instrument Telemetry & Callout Displays: 22px rounded ergonomics */
QFrame.offsetCallout {
    background-color: #26272d;
    border: 1px solid #2d2f36;
    border-radius: 22px;
    padding: 6px 12px;
}

QFrame.metricCallout {
    background-color: #26272d;
    border: 1px solid #2d2f36;
    border-radius: 22px;
    padding: 8px 12px;
}

QFrame.viewportScreen {
    background-color: #26272d;
    border: 1px solid #2d2f36;
    border-radius: 22px;
}

QFrame.optionsContainer, QFrame#frameOptions {
    background-color: #26272d;
    border: 1px solid #2d2f36;
    border-radius: 22px;
    padding: 8px 14px;
}

QFrame.sliderContainer, QFrame#frameSlider {
    background-color: #26272d;
    border: 1px solid #2d2f36;
    border-radius: 22px;
    padding: 8px 14px;
}

/* Monospace Numbers & Metrics */
QLabel.monoValue {
    background-color: transparent;
    color: #f2f3f7;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 13px;
    font-weight: 700;
    border: none;
}

QLabel.largeOffsetDisplay {
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #2d2f36;
    border-radius: 999px;
    padding: 4px 16px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 24px;
    font-weight: 800;
    letter-spacing: -0.5px;
}

/* Discrete Precision Telemetry Chips & Banners (Pills 999px) */
QLabel.diagnosisBanner {
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #2d2f36;
    border-radius: 999px;
    padding: 6px 14px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#lblTimecodeChip, QLabel.timecodeChip {
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #2d2f36;
    border-radius: 999px;
    padding: 4px 12px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    font-weight: 700;
}

/* Micro-chips and Badges (Continuous Rounded Pills: 999px) */
QLabel.systemChip {
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #2d2f36;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

QLabel.codecChip {
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #2d2f36;
    border-radius: 999px;
    padding: 2px 10px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeNeutral {
    background-color: #26272d;
    color: #9a9eac;
    border: 1px solid #2d2f36;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 10px;
    font-weight: 600;
}

QLabel.badgeSignal {
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #f2f3f7;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeRecommended, QLabel#badgeRecommended {
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #f2f3f7;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

QLabel.badgeGreen {
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #2d2f36;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeAmber {
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #2d2f36;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 10px;
    font-weight: 700;
}

/* Stream Review Gate: Two-Level Structured Stream Rows (22px rounded subcards) */
QFrame.streamRowCard {
    background-color: #26272d;
    border: 1px solid #2d2f36;
    border-radius: 22px;
}

QLabel.streamIdTag {
    background-color: #33343b;
    color: #f2f3f7;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.3px;
    border: 1px solid #2d2f36;
    border-radius: 999px;
    padding: 2px 10px;
}

QLabel.roleBadge {
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #2d2f36;
    border-radius: 999px;
    padding: 2px 12px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

QLabel.streamActionChip {
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #2d2f36;
    border-radius: 999px;
    padding: 3px 14px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
    min-width: 64px;
}

QComboBox.streamCombo {
    background-color: #1b1c20;
    color: #f2f3f7;
    border: 1px solid #2d2f36;
    border-radius: 999px;
    padding: 5px 14px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    min-height: 26px;
}

QLabel.streamDesc {
    background-color: transparent;
    color: #9a9eac;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    border: none;
}

/* Stream Arbitration Diagnostic Block */
QFrame.arbitrationCard, QFrame#frameArbitration {
    background-color: #26272d;
    border: 1px solid #2d2f36;
    border-radius: 22px;
}

/* Buttons: 999px Ergonomic Pills (#eef0f2 compat accent) */
QPushButton {
    border-radius: 999px;
    font-weight: 600;
    font-size: 12px;
    padding: 7px 18px;
}

QPushButton.btnPrimary {
    background-color: #f2f3f7;
    color: #000000;
    border: 1px solid #f2f3f7;
    font-weight: 700;
}

QPushButton.btnPrimary:hover {
    background-color: #ffffff;
    border-color: #ffffff;
}

QPushButton.btnPrimary:pressed {
    background-color: #d1d4dc;
    border-color: #d1d4dc;
}

QPushButton.btnSuccess {
    background-color: #f2f3f7;
    color: #000000;
    border: 1px solid #f2f3f7;
    font-weight: 700;
    font-size: 13px;
    padding: 8px 22px;
}

QPushButton.btnSuccess:hover {
    background-color: #ffffff;
    border-color: #ffffff;
}

QPushButton.btnSuccess:pressed {
    background-color: #d1d4dc;
    border-color: #d1d4dc;
}

QPushButton.btnSecondary {
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #2d2f36;
}

QPushButton.btnSecondary:hover {
    background-color: #33343b;
    border-color: #f2f3f7;
}

QPushButton.btnSecondary:pressed {
    background-color: #1b1c20;
    border-color: #f2f3f7;
}

QPushButton.btnDanger {
    background-color: #26272d;
    color: #9a9eac;
    border: 1px solid #2d2f36;
}

QPushButton.btnDanger:hover {
    background-color: #33343b;
    color: #f2f3f7;
    border-color: #f2f3f7;
}

/* Precision Nudge Pills */
QPushButton.btnNudge {
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #2d2f36;
    border-radius: 999px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 600;
}

QPushButton.btnNudge:hover {
    background-color: #33343b;
    border-color: #f2f3f7;
}

QPushButton.btnNudge:pressed {
    background-color: #1b1c20;
}

/* Precision Bench Markers */
QPushButton.markerBtn {
    background-color: #26272d;
    color: #9a9eac;
    border: 1px solid #2d2f36;
    border-radius: 999px;
    padding: 5px 14px;
    font-size: 11px;
    font-weight: 700;
}

QPushButton.markerBtn:hover {
    background-color: #33343b;
    color: #f2f3f7;
    border-color: #9a9eac;
}

QPushButton.markerBtn:checked {
    background-color: #f2f3f7;
    color: #000000;
    border: 1px solid #f2f3f7;
}

/* Unified Drop Zone States (24px - 28px rounded) */
QFrame#dropFrameEmpty {
    border: 1px dashed #2d2f36;
    border-radius: 28px;
    background-color: #1b1c20;
}

QFrame#dropFrameEmpty[dragOver="true"] {
    border: 1px dashed #f2f3f7;
    background-color: #26272d;
}

QFrame#dropFrameSingle {
    border: 1px solid #2d2f36;
    border-radius: 28px;
    background-color: #1b1c20;
}

/* File Card Workbench (24px rounded corners) */
QFrame.fileCardWorkbench {
    background-color: #26272d;
    border: 1px solid #2d2f36;
    border-radius: 24px;
}

/* Dividers */
QFrame.dividerLine, QFrame#crumbSep {
    background-color: #2d2f36;
    border: none;
}

/* Inputs & Comboboxes (999px Oval Pills) */
QLineEdit, QComboBox {
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #2d2f36;
    border-radius: 999px;
    padding: 6px 14px;
    font-size: 12px;
}

QLineEdit:focus, QComboBox:focus {
    border-color: #f2f3f7;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #1b1c20;
    color: #f2f3f7;
    border: 1px solid #2d2f36;
    border-radius: 14px;
    selection-background-color: #33343b;
    selection-color: #f2f3f7;
    padding: 4px;
}

/* Linear Continuous Rail Slider */
QSlider::groove:horizontal {
    height: 6px;
    background: #26272d;
    border-radius: 999px;
}

QSlider::sub-page:horizontal {
    background: #33343b;
    border-radius: 999px;
}

QSlider::handle:horizontal {
    background: #f2f3f7;
    border: 1px solid #f2f3f7;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 999px;
}

/* Progress Bar (Pill Capsule) */
QProgressBar {
    background-color: #26272d;
    border: 1px solid #2d2f36;
    border-radius: 999px;
    text-align: center;
    color: #f2f3f7;
    font-size: 11px;
    font-weight: 700;
    max-height: 16px;
}

QProgressBar::chunk {
    background-color: #f2f3f7;
    border-radius: 999px;
}

/* Checkboxes (Modern Toggle Style) */
QCheckBox {
    background-color: transparent;
    border: none;
    color: #9a9eac;
    font-size: 11px;
    spacing: 8px;
}

QCheckBox:hover {
    color: #f2f3f7;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border: 1px solid #2d2f36;
    border-radius: 6px;
    background-color: #1b1c20;
}

QCheckBox::indicator:hover {
    border-color: #9a9eac;
}

QCheckBox::indicator:checked {
    background-color: #26272d;
    border: 1px solid #9a9eac;
    image: url("__CHECK_GLYPH_PATH__");
}

/* Retractable Collapsible Section Toggle */
QPushButton#collapsibleHeaderBtn {
    background-color: transparent;
    color: #f2f3f7;
    border: none;
    font-size: 12px;
    font-weight: 700;
    text-align: left;
    padding: 4px 0;
}

/* Terminal & Log Drawer Output */
QPlainTextEdit {
    background-color: #1b1c20;
    color: #f2f3f7;
    border: 1px solid #2d2f36;
    border-radius: 18px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    padding: 8px;
}

/* Scrollbars: Minimal Rounded Rail */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #33343b;
    min-height: 24px;
    border-radius: 999px;
}

QScrollBar::handle:vertical:hover {
    background: #40424c;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #33343b;
    min-width: 24px;
    border-radius: 999px;
}

QScrollBar::handle:horizontal:hover {
    background: #40424c;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    height: 0;
}

/* Modals */
QDialog {
    background-color: #1b1c20;
    border: 1px solid #2d2f36;
    border-radius: 28px;
}
"""

# ==============================================================================
# Light Theme QSS (One UI Modern Card Ergonomics: #f1f2f6 base, #ffffff cards, #16181d text)
# Legacy compatibility tokens preserved: #f2f3f1, #191c1a, #ffffff
# ==============================================================================
LIGHT_THEME_QSS = """
/* Global Window & Typography (One UI Precision Light: #f1f2f6 base, #f2f3f1 compat) */
QWidget {
    background-color: #f1f2f6;
    color: #16181d;
    font-family: 'Inter', 'Segoe UI', 'Liberation Sans', -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #dcdfe8;
    selection-color: #16181d;
}

/* Universal Label Reset: Eradicate hard opaque backgrounds and border artifacts */
QLabel {
    background-color: transparent;
    background: transparent;
    border: none;
}

QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* Workbench Topbar: Continuous clean surface */
QWidget#workbenchTopbar {
    background-color: #ffffff;
    border-bottom: 1px solid #dcdfe8;
}

QLabel#brandTitle {
    background-color: transparent;
    color: #16181d;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: -0.4px;
    border: none;
}

QLabel#brandSubtitle {
    background-color: transparent;
    color: #6a7080;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.2px;
    border: none;
}

QLabel#topCrumb {
    background-color: transparent;
    color: #6a7080;
    font-size: 12px;
    border: none;
}

QLabel#topCrumb strong {
    color: #16181d;
    font-weight: 600;
}

/* One UI Primary Bento/Panel Cards: Generous 28px rounded corners (#ffffff) */
QFrame.panelCard, QFrame.bentoCard {
    background-color: #ffffff;
    border: 1px solid #dcdfe8;
    border-radius: 28px;
}

/* Floating Bottom Dock: Seamless 34px rounded capsule container */
QFrame#floatingDock, QFrame.floatingDock, QFrame#eventLogDrawer {
    background-color: #ffffff;
    border: 1px solid #dcdfe8;
    border-radius: 34px;
}

/* Subcards / Inset Containers: 22px rounded corners */
QFrame.subCard {
    background-color: #eceef4;
    border: 1px solid #dcdfe8;
    border-radius: 22px;
}

/* Panel Header and Headings */
QLabel.sectionIndex {
    background-color: transparent;
    color: #6a7080;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    border: none;
}

QLabel.cardTitle {
    background-color: transparent;
    color: #16181d;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: -0.2px;
    border: none;
}

QLabel.subText {
    background-color: transparent;
    color: #6a7080;
    font-size: 11px;
    border: none;
}

QLabel.dropTitle {
    background-color: transparent;
    color: #16181d;
    font-size: 14px;
    font-weight: 700;
    border: none;
}

QLabel.logTitle {
    background-color: transparent;
    color: #16181d;
    font-size: 12px;
    font-weight: 700;
    border: none;
}

QLabel.eyebrowText {
    background-color: transparent;
    color: #6a7080;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.0px;
    border: none;
}

/* Instrument Telemetry & Callout Displays: 22px rounded ergonomics */
QFrame.offsetCallout {
    background-color: #eceef4;
    border: 1px solid #dcdfe8;
    border-radius: 22px;
    padding: 6px 12px;
}

QFrame.metricCallout {
    background-color: #eceef4;
    border: 1px solid #dcdfe8;
    border-radius: 22px;
    padding: 8px 12px;
}

QFrame.viewportScreen {
    background-color: #ffffff;
    border: 1px solid #dcdfe8;
    border-radius: 22px;
}

QFrame.optionsContainer, QFrame#frameOptions {
    background-color: #eceef4;
    border: 1px solid #dcdfe8;
    border-radius: 22px;
    padding: 8px 14px;
}

QFrame.sliderContainer, QFrame#frameSlider {
    background-color: #eceef4;
    border: 1px solid #dcdfe8;
    border-radius: 22px;
    padding: 8px 14px;
}

/* Monospace Numbers & Metrics (#191c1a compat) */
QLabel.monoValue {
    background-color: transparent;
    color: #16181d;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 13px;
    font-weight: 700;
    border: none;
}

QLabel.largeOffsetDisplay {
    background-color: #eceef4;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 999px;
    padding: 4px 16px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 24px;
    font-weight: 800;
    letter-spacing: -0.5px;
}

/* Discrete Precision Telemetry Chips & Banners (Pills 999px) */
QLabel.diagnosisBanner {
    background-color: #eceef4;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 999px;
    padding: 6px 14px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#lblTimecodeChip, QLabel.timecodeChip {
    background-color: #eceef4;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 999px;
    padding: 4px 12px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    font-weight: 700;
}

/* Micro-chips and Badges (Continuous Rounded Pills: 999px) */
QLabel.systemChip {
    background-color: #eceef4;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

QLabel.codecChip {
    background-color: #eceef4;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 999px;
    padding: 2px 10px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeNeutral {
    background-color: #eceef4;
    color: #6a7080;
    border: 1px solid #dcdfe8;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 10px;
    font-weight: 600;
}

QLabel.badgeSignal {
    background-color: #eceef4;
    color: #16181d;
    border: 1px solid #16181d;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeRecommended, QLabel#badgeRecommended {
    background-color: #eceef4;
    color: #16181d;
    border: 1px solid #16181d;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

QLabel.badgeGreen {
    background-color: #eceef4;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeAmber {
    background-color: #eceef4;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 10px;
    font-weight: 700;
}

/* Stream Review Gate: Two-Level Structured Stream Rows (22px rounded subcards) */
QFrame.streamRowCard {
    background-color: #eceef4;
    border: 1px solid #dcdfe8;
    border-radius: 22px;
}

QLabel.streamIdTag {
    background-color: #e1e4ed;
    color: #16181d;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.3px;
    border: 1px solid #dcdfe8;
    border-radius: 999px;
    padding: 2px 10px;
}

QLabel.roleBadge {
    background-color: #eceef4;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 999px;
    padding: 2px 12px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

QLabel.streamActionChip {
    background-color: #eceef4;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 999px;
    padding: 3px 14px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
    min-width: 64px;
}

QComboBox.streamCombo {
    background-color: #ffffff;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 999px;
    padding: 5px 14px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    min-height: 26px;
}

QLabel.streamDesc {
    background-color: transparent;
    color: #6a7080;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    border: none;
}

/* Stream Arbitration Diagnostic Block */
QFrame.arbitrationCard, QFrame#frameArbitration {
    background-color: #eceef4;
    border: 1px solid #dcdfe8;
    border-radius: 22px;
}

/* Buttons: 999px Ergonomic Pills */
QPushButton {
    border-radius: 999px;
    font-weight: 600;
    font-size: 12px;
    padding: 7px 18px;
}

QPushButton.btnPrimary {
    background-color: #16181d;
    color: #ffffff;
    border: 1px solid #16181d;
    font-weight: 700;
}

QPushButton.btnPrimary:hover {
    background-color: #2d2f36;
    border-color: #2d2f36;
}

QPushButton.btnPrimary:pressed {
    background-color: #40424c;
    border-color: #40424c;
}

QPushButton.btnSuccess {
    background-color: #16181d;
    color: #ffffff;
    border: 1px solid #16181d;
    font-weight: 700;
    font-size: 13px;
    padding: 8px 22px;
}

QPushButton.btnSuccess:hover {
    background-color: #2d2f36;
    border-color: #2d2f36;
}

QPushButton.btnSuccess:pressed {
    background-color: #40424c;
    border-color: #40424c;
}

QPushButton.btnSecondary {
    background-color: #eceef4;
    color: #16181d;
    border: 1px solid #dcdfe8;
}

QPushButton.btnSecondary:hover {
    background-color: #e1e4ed;
    border-color: #16181d;
}

QPushButton.btnSecondary:pressed {
    background-color: #dcdfe8;
    border-color: #16181d;
}

QPushButton.btnDanger {
    background-color: #eceef4;
    color: #6a7080;
    border: 1px solid #dcdfe8;
}

QPushButton.btnDanger:hover {
    background-color: #e1e4ed;
    color: #16181d;
    border-color: #16181d;
}

/* Precision Nudge Pills */
QPushButton.btnNudge {
    background-color: #eceef4;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 999px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 600;
}

QPushButton.btnNudge:hover {
    background-color: #e1e4ed;
    border-color: #16181d;
}

QPushButton.btnNudge:pressed {
    background-color: #dcdfe8;
}

/* Precision Bench Markers */
QPushButton.markerBtn {
    background-color: #eceef4;
    color: #6a7080;
    border: 1px solid #dcdfe8;
    border-radius: 999px;
    padding: 5px 14px;
    font-size: 11px;
    font-weight: 700;
}

QPushButton.markerBtn:hover {
    background-color: #ffffff;
    color: #16181d;
    border-color: #16181d;
}

QPushButton.markerBtn:checked {
    background-color: #16181d;
    color: #ffffff;
    border: 1px solid #16181d;
}

/* Unified Drop Zone States (24px - 28px rounded) */
QFrame#dropFrameEmpty {
    border: 1px dashed #dcdfe8;
    border-radius: 28px;
    background-color: #ffffff;
}

QFrame#dropFrameEmpty[dragOver="true"] {
    border: 1px dashed #16181d;
    background-color: #eceef4;
}

QFrame#dropFrameSingle {
    border: 1px solid #dcdfe8;
    border-radius: 28px;
    background-color: #ffffff;
}

/* File Card Workbench (24px rounded corners) */
QFrame.fileCardWorkbench {
    background-color: #eceef4;
    border: 1px solid #dcdfe8;
    border-radius: 24px;
}

/* Dividers */
QFrame.dividerLine, QFrame#crumbSep {
    background-color: #dcdfe8;
    border: none;
}

/* Inputs & Comboboxes (999px Oval Pills) */
QLineEdit, QComboBox {
    background-color: #ffffff;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 999px;
    padding: 6px 14px;
    font-size: 12px;
}

QLineEdit:focus, QComboBox:focus {
    border-color: #16181d;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 14px;
    selection-background-color: #e1e4ed;
    selection-color: #16181d;
    padding: 4px;
}

/* Linear Continuous Rail Slider */
QSlider::groove:horizontal {
    height: 6px;
    background: #eceef4;
    border-radius: 999px;
}

QSlider::sub-page:horizontal {
    background: #dcdfe8;
    border-radius: 999px;
}

QSlider::handle:horizontal {
    background: #16181d;
    border: 1px solid #16181d;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 999px;
}

/* Progress Bar (Pill Capsule) */
QProgressBar {
    background-color: #eceef4;
    border: 1px solid #dcdfe8;
    border-radius: 999px;
    text-align: center;
    color: #16181d;
    font-size: 11px;
    font-weight: 700;
    max-height: 16px;
}

QProgressBar::chunk {
    background-color: #16181d;
    border-radius: 999px;
}

/* Checkboxes (Modern Toggle Style) */
QCheckBox {
    background-color: transparent;
    border: none;
    color: #6a7080;
    font-size: 11px;
    spacing: 8px;
}

QCheckBox:hover {
    color: #16181d;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border: 1px solid #dcdfe8;
    border-radius: 6px;
    background-color: #ffffff;
}

QCheckBox::indicator:hover {
    border-color: #6a7080;
}

QCheckBox::indicator:checked {
    background-color: #eceef4;
    border: 1px solid #6a7080;
    image: url("__CHECK_GLYPH_PATH__");
}

/* Retractable Collapsible Section Toggle */
QPushButton#collapsibleHeaderBtn {
    background-color: transparent;
    color: #16181d;
    border: none;
    font-size: 12px;
    font-weight: 700;
    text-align: left;
    padding: 4px 0;
}

/* Terminal & Log Drawer Output */
QPlainTextEdit {
    background-color: #ffffff;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 18px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    padding: 8px;
}

/* Scrollbars: Minimal Rounded Rail */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #dcdfe8;
    min-height: 24px;
    border-radius: 999px;
}

QScrollBar::handle:vertical:hover {
    background: #6a7080;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #dcdfe8;
    min-width: 24px;
    border-radius: 999px;
}

QScrollBar::handle:horizontal:hover {
    background: #6a7080;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    height: 0;
}

/* Modals */
QDialog {
    background-color: #ffffff;
    border: 1px solid #dcdfe8;
    border-radius: 28px;
}
"""

DARK_THEME_QSS = DARK_THEME_QSS.replace("__CHECK_GLYPH_PATH__", get_check_icon_path())
LIGHT_THEME_QSS = LIGHT_THEME_QSS.replace("__CHECK_GLYPH_PATH__", get_check_icon_path())


def get_theme_stylesheet(mode: Literal["dark", "light"] = "dark") -> str:
    """Returns the QSS stylesheet for the requested precision bench theme."""
    return DARK_THEME_QSS if mode == "dark" else LIGHT_THEME_QSS


def get_application_stylesheet(mode: Literal["dark", "light"] = "dark") -> str:
    """Backwards-compatible alias for get_theme_stylesheet."""
    return get_theme_stylesheet(mode)


def get_theme_qss(mode: Literal["dark", "light"] = "dark") -> str:
    """Backwards-compatible alias for get_theme_stylesheet."""
    return get_theme_stylesheet(mode)


def apply_workbench_theme(widget, mode: Literal["dark", "light"] = "dark"):
    """Applies the precision bench monochrome theme to the target application or widget."""
    widget.setStyleSheet(get_theme_stylesheet(mode))


def apply_theme(target_widget, mode: Literal["dark", "light"] = "dark"):
    """Backwards-compatible alias for apply_workbench_theme."""
    apply_workbench_theme(target_widget, mode)


def apply_one_ui_monochrome_theme(app_instance: Optional[QApplication], mode: Literal["dark", "light"] = "dark") -> None:
    """Applies the modern One UI monochrome theme with continuous rounded surfaces."""
    if app_instance is not None:
        app_instance.setStyleSheet(get_theme_stylesheet(mode))


def get_telemetry_badge_style(mode: Literal["dark", "light"] = "dark") -> str:
    """Returns CSS styles for telemetry callouts and contrast badges."""
    if mode == "dark":
        return """
        QFrame.offsetCallout {
            background-color: #26272d;
            border: 1px solid #2d2f36;
            border-radius: 22px;
            padding: 6px 12px;
        }
        QFrame.metricCallout {
            background-color: #26272d;
            border: 1px solid #2d2f36;
            border-radius: 22px;
            padding: 8px 12px;
        }
        """
    return """
    QFrame.offsetCallout {
        background-color: #eceef4;
        border: 1px solid #dcdfe8;
        border-radius: 22px;
        padding: 6px 12px;
    }
    QFrame.metricCallout {
        background-color: #eceef4;
        border: 1px solid #dcdfe8;
        border-radius: 22px;
        padding: 8px 12px;
    }
    """


def get_player_viewport_style(mode: Literal["dark", "light"] = "dark") -> str:
    """Returns CSS styles for the preview monitor and lip-sync player controls."""
    if mode == "dark":
        return """
        QFrame.viewportScreen {
            background-color: #26272d;
            border: 1px solid #2d2f36;
            border-radius: 22px;
        }
        QPushButton.markerBtn {
            background-color: #26272d;
            color: #9a9eac;
            border: 1px solid #2d2f36;
            border-radius: 999px;
            padding: 5px 14px;
            font-size: 11px;
            font-weight: 700;
        }
        QPushButton.markerBtn:hover {
            background-color: #33343b;
            color: #f2f3f7;
            border-color: #9a9eac;
        }
        QPushButton.markerBtn:checked {
            background-color: #f2f3f7;
            color: #000000;
            border: 1px solid #f2f3f7;
        }
        """
    return """
    QFrame.viewportScreen {
        background-color: #ffffff;
        border: 1px solid #dcdfe8;
        border-radius: 22px;
    }
    QPushButton.markerBtn {
        background-color: #eceef4;
        color: #6a7080;
        border: 1px solid #dcdfe8;
        border-radius: 999px;
        padding: 5px 14px;
        font-size: 11px;
        font-weight: 700;
    }
    QPushButton.markerBtn:hover {
        background-color: #ffffff;
        color: #16181d;
        border-color: #16181d;
    }
    QPushButton.markerBtn:checked {
        background-color: #16181d;
        color: #ffffff;
        border: 1px solid #16181d;
    }
    """


def get_clean_badge_style(radius: int = 999, bg: str = "#26272d", border: str = "#2d2f36") -> str:
    """Returns CSS properties for clean, high-density micro-badges with smooth border-radius."""
    return f"""
        background-color: {bg};
        border: 1px solid {border};
        border-radius: {radius}px;
        padding: 3px 12px;
    """


def get_telemetry_display_style(is_accent: bool = False) -> str:
    """Returns CSS properties for precision telemetry boxes with rounded corners and no hard black backgrounds."""
    if is_accent:
        return """
            background-color: #26272d;
            color: #f2f3f7;
            border: 1px solid #f2f3f7;
            border-radius: 999px;
            padding: 4px 14px;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
            font-weight: 700;
        """
    return """
        background-color: #26272d;
        color: #f2f3f7;
        border: 1px solid #2d2f36;
        border-radius: 999px;
        padding: 4px 14px;
        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
        font-weight: 700;
    """


def get_topbar_brand_style() -> str:
    """Returns CSS styling for the topbar branding block with zero hard backgrounds and clean vector alignment."""
    return """
        QLabel#brandTitle {
            background-color: transparent;
            color: #f2f3f7;
            font-size: 15px;
            font-weight: 800;
            letter-spacing: -0.4px;
            border: none;
        }
        QLabel#brandSubtitle {
            background-color: transparent;
            color: #9a9eac;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
            font-size: 9px;
            font-weight: 600;
            letter-spacing: 1.2px;
            border: none;
        }
        QLabel#topCrumb {
            background-color: transparent;
            color: #9a9eac;
            font-size: 12px;
            border: none;
            padding-left: 2px;
        }
        QLabel#topCrumb strong {
            color: #f2f3f7;
            font-weight: 600;
        }
    """


def get_role_badge_style(role_type: str) -> str:
    """Returns CSS/QSS styling string for stream role classification badges."""
    rt = role_type.lower()
    if "recomenda" in rt or "fidelidade" in rt or "audiophile" in rt:
        return "border-radius: 999px; padding: 2px 12px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;"
    elif "melhor" in rt or "imagem" in rt or "video" in rt:
        return "border-radius: 999px; padding: 2px 12px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;"
    elif "portugu" in rt or "alvo" in rt or "target" in rt or "manual" in rt:
        return "border-radius: 999px; padding: 2px 12px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;"
    else:
        return "border-radius: 999px; padding: 2px 12px; font-size: 10px; font-weight: 600; letter-spacing: 0.5px;"


def get_action_chip_style(action_type: str) -> str:
    """Returns CSS/QSS styling string for stream action/state chips (Copy, Align)."""
    return "border-radius: 999px; padding: 3px 14px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px; min-width: 64px;"
