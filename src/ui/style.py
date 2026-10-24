"""One UI 8.5 presentation styling for SyncFrame desktop workbench."""

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
            pen = QPen(QColor(47, 177, 107), 2.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(QPoint(3, 9), QPoint(7, 13))
            painter.drawLine(QPoint(7, 13), QPoint(14, 5))
            painter.end()
            img.save(CHECK_GLYPH_PATH)
        except Exception:
            pass
    return CHECK_GLYPH_PATH.replace("\\", "/")


def get_switch_icon_path(is_on: bool, mode: Literal["dark", "light"] = "dark") -> str:
    """Generates crisp One UI rounded toggle switch capsule assets."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    filename = f"switch_{mode}_{'on' if is_on else 'off'}.png"
    filepath = os.path.join(ASSETS_DIR, filename)
    if not os.path.isfile(filepath):
        try:
            from PySide6.QtGui import QImage, QPainter, QColor, QBrush
            from PySide6.QtCore import Qt, QRectF
            img = QImage(46, 28, QImage.Format_ARGB32)
            img.fill(Qt.transparent)
            painter = QPainter(img)
            painter.setRenderHint(QPainter.Antialiasing, True)

            # Capsule background
            if is_on:
                bg_col = QColor("#5b9bff" if mode == "dark" else "#3e82f7")
            else:
                bg_col = QColor("#33343b" if mode == "dark" else "#e1e4ed")

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(bg_col))
            painter.drawRoundedRect(QRectF(0, 0, 46, 28), 14, 14)

            # Thumb circle
            thumb_col = QColor("#ffffff")
            thumb_x = 22 if is_on else 4
            thumb_y = 4
            painter.setBrush(QBrush(thumb_col))
            painter.drawEllipse(QRectF(thumb_x, thumb_y, 20, 20))
            painter.end()
            img.save(filepath)
        except Exception:
            pass
    return filepath.replace("\\", "/")


def get_theme_tokens(mode: Literal["dark", "light"] = "dark") -> Dict[str, str]:
    """Returns the atomic color tokens for the specified theme."""
    if mode == "dark":
        return {
            "bg_base": "#000000",
            "bg_card": "#1b1c20",
            "bg_soft": "#26272d",
            "bg_soft2": "#33343b",
            "text_primary": "#f2f3f7",
            "text_secondary": "#9a9eac",
            "accent": "#5b9bff",
            "accent_soft": "#1e3157",
            "accent_text": "#06132b",
            "ok": "#2fb16b",
            "warn": "#e8963a",
            "border_subtle": "#2d2f36",
        }
    return {
        "bg_base": "#f1f2f6",
        "bg_card": "#ffffff",
        "bg_soft": "#eceef4",
        "bg_soft2": "#e1e4ed",
        "text_primary": "#16181d",
        "text_secondary": "#6a7080",
        "accent": "#3e82f7",
        "accent_soft": "#dce8ff",
        "accent_text": "#ffffff",
        "ok": "#2fb16b",
        "warn": "#e8963a",
        "border_subtle": "#dcdfe8",
    }


# ==============================================================================
# Dark Theme QSS (One UI 8.5: #000000 base, #1b1c20 cards, #5b9bff accent)
# Compatibility tokens: #0a0b0d, #111317, #eef0f2
# ==============================================================================
DARK_THEME_QSS = """
/* Compatibility tokens: #0a0b0d, #111317, #eef0f2 */

/* Global Window & Typography (One UI 8.5 Dark) */
QWidget {
    background-color: #000000;
    color: #f2f3f7;
    font-family: 'Figtree', 'Inter', 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    selection-background-color: #33343b;
    selection-color: #f2f3f7;
}

QLabel {
    background-color: transparent;
    border: none;
}

QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* Header Area (One UI Topbar) */
QWidget#workbenchTopbar, QWidget#topHeader {
    background-color: transparent;
    border: none;
}

QLabel#appTitle, QLabel#brandTitle {
    font-size: 34px;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #f2f3f7;
    line-height: 1.05;
}

QLabel#appSubtitle, QLabel#brandSubtitle {
    color: #9a9eac;
    font-size: 13px;
    font-weight: 500;
    margin-top: 4px;
}

QLabel#topCrumb {
    color: #9a9eac;
    font-size: 12px;
}

/* Header Pills (One UI Status & Actions) */
QFrame.pill, QLabel.pill, QPushButton.pill {
    border-radius: 999px;
    background-color: #1b1c20;
    color: #f2f3f7;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
    border: none;
}

QFrame.pill:hover, QPushButton.pill:hover {
    background-color: #26272d;
}

QFrame.pillSoft, QLabel.pillSoft {
    border-radius: 999px;
    background-color: #26272d;
    color: #9a9eac;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
    border: none;
}

QLabel.greenDot {
    min-width: 8px;
    max-width: 8px;
    min-height: 8px;
    max-height: 8px;
    border-radius: 4px;
    background-color: #2fb16b;
}

/* One UI Primary Cards: 32px rounded radius */
QFrame.card, QFrame.bentoCard, QFrame.panelCard, QFrame#panelCardRemux {
    background-color: #1b1c20;
    border-radius: 32px;
    border: none;
}

QLabel.cardHeaderTitle, QLabel.cardTitle, QLabel#cardTitle {
    font-size: 19px;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: #f2f3f7;
}

QLabel.hint, QLabel.subText {
    color: #9a9eac;
    font-size: 13px;
}

QLabel.sectionIndex {
    color: #9a9eac;
    font-weight: 700;
}

/* One UI Tags and Pills */
QLabel.tag {
    border-radius: 999px;
    background-color: #1e3157;
    color: #5b9bff;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 700;
}

QLabel.tagNeutral, QLabel.tagN, QLabel.badgeNeutral, QLabel.codecChip, QLabel.systemChip {
    border-radius: 999px;
    background-color: #26272d;
    color: #9a9eac;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
}

QLabel.tagGreen, QLabel.tagG, QLabel.badgeGreen, QLabel.badgeSignal {
    border-radius: 999px;
    background-color: rgba(47, 177, 107, 0.16);
    color: #2fb16b;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 700;
}

QLabel.tagWarn, QLabel.badgeAmber {
    border-radius: 999px;
    background-color: rgba(232, 150, 58, 0.16);
    color: #e8963a;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 700;
}

QLabel.badgeRecommended, QLabel#badgeRecommended {
    border-radius: 999px;
    background-color: #1e3157;
    color: #5b9bff;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 700;
}

/* Buttons (One UI 999px Pills) */
QPushButton.btn {
    border-radius: 999px;
    background-color: #26272d;
    color: #f2f3f7;
    padding: 10px 18px;
    font-weight: 600;
    font-size: 13px;
    border: none;
}

QPushButton.btn:hover {
    background-color: #33343b;
}

QPushButton.btnPrimary, QPushButton.btnPr, QPushButton.btnSuccess {
    border-radius: 999px;
    background-color: #5b9bff;
    color: #06132b;
    padding: 14px 28px;
    font-weight: 700;
    font-size: 15px;
    border: none;
}

QPushButton.btnPrimary:hover, QPushButton.btnSuccess:hover {
    background-color: #70a9ff;
}

QPushButton.btnPrimary:pressed, QPushButton.btnSuccess:pressed {
    background-color: #4a8ae6;
}

QPushButton.btnSm, QPushButton.btnSecondary, QPushButton.btnDanger {
    border-radius: 999px;
    background-color: #26272d;
    color: #f2f3f7;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 600;
    border: none;
}

QPushButton.btnSm:hover, QPushButton.btnSecondary:hover {
    background-color: #33343b;
}

/* File Box (Pair Grid) */
QFrame.fileBox, QFrame.fileCardWorkbench, QFrame.subCard {
    background-color: #26272d;
    border-radius: 24px;
    border: none;
}

QLabel.fileRole, QLabel.eyebrowText {
    color: #9a9eac;
    font-size: 13px;
    font-weight: 500;
}

QLabel.fileName {
    font-size: 15px;
    font-weight: 600;
    color: #f2f3f7;
}

QLabel.fileMeta {
    color: #9a9eac;
    font-size: 13px;
}

/* Dubbing Container (.dub) */
QFrame.dubBox, QFrame.arbitrationCard, QFrame#frameArbitration {
    background-color: #1e3157;
    border-radius: 24px;
    border: none;
}

QLabel.dubTitle {
    font-size: 13.5px;
    font-weight: 700;
    color: #f2f3f7;
}

QLabel.dubDesc {
    font-size: 12.5px;
    color: #9a9eac;
}

/* Track Row (.trk) */
QFrame.trackRow, QFrame.streamRowCard {
    background-color: #26272d;
    border-radius: 26px;
    border: none;
}

QFrame.trackRow[recommended="true"], QFrame.trackRowRec {
    border: 2px solid #5b9bff;
}

QLabel.trackIdBox, QLabel.streamIdTag {
    min-width: 44px;
    max-width: 44px;
    min-height: 44px;
    max-height: 44px;
    border-radius: 16px;
    background-color: #1b1c20;
    color: #f2f3f7;
    font-weight: 700;
    font-size: 14px;
    qproperty-alignment: AlignCenter;
}

QLabel.trackIdBox[recommended="true"] {
    background-color: #5b9bff;
    color: #06132b;
}

QLabel.trackTitle {
    font-size: 14px;
    font-weight: 600;
    color: #f2f3f7;
}

QLabel.trackDesc, QLabel.streamDesc {
    font-size: 13px;
    color: #9a9eac;
}

QLabel.roleBadge {
    border-radius: 999px;
    background-color: #1b1c20;
    color: #f2f3f7;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
}

QLabel.streamActionChip {
    border-radius: 999px;
    background-color: #1e3157;
    color: #5b9bff;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 700;
    min-width: 64px;
}

/* Audit Pill Row (.audit) */
QFrame.auditPill, QFrame#frameAudioAudit {
    background-color: #26272d;
    border-radius: 999px;
    border: none;
}

/* Option Pill Rows (.opt) */
QFrame.optRow, QFrame.optionsContainer, QFrame#frameOptions {
    background-color: #26272d;
    border-radius: 999px;
    border: none;
}

QLabel.optLabel {
    font-size: 13.5px;
    font-weight: 500;
    color: #f2f3f7;
}

/* Toggle Switches (.sw) via QCheckBox */
QCheckBox {
    background-color: transparent;
    border: none;
    color: #f2f3f7;
    font-size: 13px;
    font-weight: 500;
    spacing: 10px;
}

QCheckBox::indicator {
    width: 46px;
    height: 28px;
    background: transparent;
}

QCheckBox::indicator:unchecked {
    image: url("__SWITCH_DARK_OFF__");
}

QCheckBox::indicator:checked {
    image: url("__SWITCH_DARK_ON__");
}

/* Output Path Pill (.out) */
QFrame.outPill {
    background-color: #26272d;
    border-radius: 999px;
    border: none;
}

QLineEdit.outPath, QLineEdit {
    background: transparent;
    color: #f2f3f7;
    font-size: 13px;
    border: none;
    padding-left: 10px;
}

QComboBox {
    background-color: #1b1c20;
    color: #f2f3f7;
    border-radius: 999px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
    border: none;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #1b1c20;
    color: #f2f3f7;
    border-radius: 16px;
    padding: 4px;
    selection-background-color: #33343b;
    selection-color: #f2f3f7;
}

/* Progress Bar (.prog) */
QProgressBar {
    background-color: #33343b;
    border-radius: 7px;
    max-height: 14px;
    text-align: center;
    color: transparent;
    border: none;
}

QProgressBar::chunk {
    background-color: #5b9bff;
    border-radius: 7px;
}

QLabel.progPct {
    font-size: 14px;
    font-weight: 700;
    color: #f2f3f7;
}

/* Offset Display Box (.off) */
QFrame.offBox, QFrame.offsetCallout {
    background-color: #26272d;
    border-radius: 28px;
    border: none;
}

QLabel.largeOffsetDisplay {
    font-size: 42px;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #f2f3f7;
    background: transparent;
    border: none;
}

/* Check glyph compatibility: __CHECK_GLYPH_PATH__ */
QCheckBox.checkGlyph::indicator:checked {
    image: url("__CHECK_GLYPH_PATH__");
}

/* Linear Rail Slider (.sl) */
QFrame.sliderContainer, QFrame#frameSlider {
    background: transparent;
    border: none;
}

QSlider::groove:horizontal {
    height: 12px;
    background: #33343b;
    border-radius: 6px;
}

QSlider::sub-page:horizontal {
    background: #5b9bff;
    border-radius: 6px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 3px solid #5b9bff;
    width: 24px;
    height: 24px;
    margin-top: -6px;
    margin-bottom: -6px;
    border-radius: 12px;
}

/* Step Nudge Buttons (.steps) */
QPushButton.stepBtn, QPushButton.btnNudge {
    background-color: #26272d;
    border-radius: 999px;
    padding: 10px 0;
    font-size: 13px;
    font-weight: 600;
    color: #f2f3f7;
    border: none;
}

QPushButton.stepBtn:hover, QPushButton.btnNudge:hover {
    background-color: #33343b;
}

/* Metrics Grid (.mets) */
QFrame.metBox, QFrame.metricCallout {
    background-color: #26272d;
    border-radius: 24px;
    border: none;
}

QLabel.metVal, QLabel.monoValue {
    font-size: 20px;
    font-weight: 700;
    color: #f2f3f7;
}

/* Note Pill (.note) */
QFrame.notePill {
    background-color: #26272d;
    border-radius: 999px;
    border: none;
}

/* Viewport Monitor (.view) */
QFrame.viewportScreen, QFrame.viewBox {
    background-color: #0c0d10;
    border-radius: 28px;
    border: none;
}

QLabel#lblTimecodeChip, QLabel.timecodeChip, QLabel.tc {
    background-color: rgba(255, 255, 255, 0.14);
    color: #ffffff;
    border-radius: 999px;
    padding: 5px 14px;
    font-weight: 600;
    font-size: 13px;
}

/* Marker Buttons (.mk) */
QPushButton.markerBtn {
    background-color: #26272d;
    border-radius: 999px;
    padding: 12px 0;
    font-weight: 600;
    color: #9a9eac;
    font-size: 13px;
    border: none;
}

QPushButton.markerBtn:hover {
    background-color: #33343b;
    color: #f2f3f7;
}

QPushButton.markerBtn:checked, QPushButton.markerBtn.on {
    background-color: #5b9bff;
    color: #06132b;
}

/* Floating Dock (.dock) */
QFrame.floatingDock, QFrame#floatingDock, QFrame#eventLogDrawer {
    background-color: #1b1c20;
    border-radius: 34px;
    border: none;
}

QLabel.logTitle {
    font-size: 14px;
    font-weight: 700;
    color: #f2f3f7;
}

QPlainTextEdit {
    background-color: #1b1c20;
    color: #9a9eac;
    border: none;
    border-radius: 18px;
    font-size: 13px;
    padding: 8px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
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

/* Empty Drop Zone */
QFrame#dropFrameEmpty {
    border: 2px dashed #33343b;
    border-radius: 32px;
    background-color: #1b1c20;
}

QFrame#dropFrameEmpty[dragOver="true"] {
    border: 2px dashed #5b9bff;
    background-color: #26272d;
}

QFrame#dropFrameSingle {
    border: 1px solid #33343b;
    border-radius: 32px;
    background-color: #1b1c20;
}
"""

# ==============================================================================
# Light Theme QSS (One UI 8.5: #f1f2f6 base, #ffffff cards, #3e82f7 accent)
# Compatibility tokens: #f2f3f1, #191c1a, #ffffff
# ==============================================================================
LIGHT_THEME_QSS = """
/* Compatibility tokens: #f2f3f1, #191c1a, #ffffff */

/* Global Window & Typography (One UI 8.5 Light) */
QWidget {
    background-color: #f1f2f6;
    color: #16181d;
    font-family: 'Figtree', 'Inter', 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    selection-background-color: #dcdfe8;
    selection-color: #16181d;
}

QLabel {
    background-color: transparent;
    border: none;
}

QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* Header Area (One UI Topbar) */
QWidget#workbenchTopbar, QWidget#topHeader {
    background-color: transparent;
    border: none;
}

QLabel#appTitle, QLabel#brandTitle {
    font-size: 34px;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #16181d;
    line-height: 1.05;
}

QLabel#appSubtitle, QLabel#brandSubtitle {
    color: #6a7080;
    font-size: 13px;
    font-weight: 500;
    margin-top: 4px;
}

QLabel#topCrumb {
    color: #6a7080;
    font-size: 12px;
}

/* Header Pills (One UI Status & Actions) */
QFrame.pill, QLabel.pill, QPushButton.pill {
    border-radius: 999px;
    background-color: #ffffff;
    color: #16181d;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
    border: none;
}

QFrame.pill:hover, QPushButton.pill:hover {
    background-color: #eceef4;
}

QFrame.pillSoft, QLabel.pillSoft {
    border-radius: 999px;
    background-color: #eceef4;
    color: #6a7080;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
    border: none;
}

QLabel.greenDot {
    min-width: 8px;
    max-width: 8px;
    min-height: 8px;
    max-height: 8px;
    border-radius: 4px;
    background-color: #2fb16b;
}

/* One UI Primary Cards: 32px rounded radius */
QFrame.card, QFrame.bentoCard, QFrame.panelCard, QFrame#panelCardRemux {
    background-color: #ffffff;
    border-radius: 32px;
    border: none;
}

QLabel.cardHeaderTitle, QLabel.cardTitle, QLabel#cardTitle {
    font-size: 19px;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: #16181d;
}

QLabel.hint, QLabel.subText {
    color: #6a7080;
    font-size: 13px;
}

QLabel.sectionIndex {
    color: #6a7080;
    font-weight: 700;
}

/* One UI Tags and Pills */
QLabel.tag {
    border-radius: 999px;
    background-color: #dce8ff;
    color: #3e82f7;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 700;
}

QLabel.tagNeutral, QLabel.tagN, QLabel.badgeNeutral, QLabel.codecChip, QLabel.systemChip {
    border-radius: 999px;
    background-color: #eceef4;
    color: #6a7080;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
}

QLabel.tagGreen, QLabel.tagG, QLabel.badgeGreen, QLabel.badgeSignal {
    border-radius: 999px;
    background-color: rgba(47, 177, 107, 0.16);
    color: #2fb16b;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 700;
}

QLabel.tagWarn, QLabel.badgeAmber {
    border-radius: 999px;
    background-color: rgba(232, 150, 58, 0.16);
    color: #e8963a;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 700;
}

QLabel.badgeRecommended, QLabel#badgeRecommended {
    border-radius: 999px;
    background-color: #dce8ff;
    color: #3e82f7;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 700;
}

/* Buttons (One UI 999px Pills) */
QPushButton.btn {
    border-radius: 999px;
    background-color: #eceef4;
    color: #16181d;
    padding: 10px 18px;
    font-weight: 600;
    font-size: 13px;
    border: none;
}

QPushButton.btn:hover {
    background-color: #e1e4ed;
}

QPushButton.btnPrimary, QPushButton.btnPr, QPushButton.btnSuccess {
    border-radius: 999px;
    background-color: #3e82f7;
    color: #ffffff;
    padding: 14px 28px;
    font-weight: 700;
    font-size: 15px;
    border: none;
}

QPushButton.btnPrimary:hover, QPushButton.btnSuccess:hover {
    background-color: #5593f9;
}

QPushButton.btnPrimary:pressed, QPushButton.btnSuccess:pressed {
    background-color: #2c72e8;
}

QPushButton.btnSm, QPushButton.btnSecondary, QPushButton.btnDanger {
    border-radius: 999px;
    background-color: #eceef4;
    color: #16181d;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 600;
    border: none;
}

QPushButton.btnSm:hover, QPushButton.btnSecondary:hover {
    background-color: #e1e4ed;
}

/* File Box (Pair Grid) */
QFrame.fileBox, QFrame.fileCardWorkbench, QFrame.subCard {
    background-color: #eceef4;
    border-radius: 24px;
    border: none;
}

QLabel.fileRole, QLabel.eyebrowText {
    color: #6a7080;
    font-size: 13px;
    font-weight: 500;
}

QLabel.fileName {
    font-size: 15px;
    font-weight: 600;
    color: #16181d;
}

QLabel.fileMeta {
    color: #6a7080;
    font-size: 13px;
}

/* Dubbing Container (.dub) */
QFrame.dubBox, QFrame.arbitrationCard, QFrame#frameArbitration {
    background-color: #dce8ff;
    border-radius: 24px;
    border: none;
}

QLabel.dubTitle {
    font-size: 13.5px;
    font-weight: 700;
    color: #16181d;
}

QLabel.dubDesc {
    font-size: 12.5px;
    color: #6a7080;
}

/* Track Row (.trk) */
QFrame.trackRow, QFrame.streamRowCard {
    background-color: #eceef4;
    border-radius: 26px;
    border: none;
}

QFrame.trackRow[recommended="true"], QFrame.trackRowRec {
    border: 2px solid #3e82f7;
}

QLabel.trackIdBox, QLabel.streamIdTag {
    min-width: 44px;
    max-width: 44px;
    min-height: 44px;
    max-height: 44px;
    border-radius: 16px;
    background-color: #ffffff;
    color: #16181d;
    font-weight: 700;
    font-size: 14px;
    qproperty-alignment: AlignCenter;
}

QLabel.trackIdBox[recommended="true"] {
    background-color: #3e82f7;
    color: #ffffff;
}

QLabel.trackTitle {
    font-size: 14px;
    font-weight: 600;
    color: #16181d;
}

QLabel.trackDesc, QLabel.streamDesc {
    font-size: 13px;
    color: #6a7080;
}

QLabel.roleBadge {
    border-radius: 999px;
    background-color: #ffffff;
    color: #16181d;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
}

QLabel.streamActionChip {
    border-radius: 999px;
    background-color: #dce8ff;
    color: #3e82f7;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 700;
    min-width: 64px;
}

/* Audit Pill Row (.audit) */
QFrame.auditPill, QFrame#frameAudioAudit {
    background-color: #eceef4;
    border-radius: 999px;
    border: none;
}

/* Option Pill Rows (.opt) */
QFrame.optRow, QFrame.optionsContainer, QFrame#frameOptions {
    background-color: #eceef4;
    border-radius: 999px;
    border: none;
}

QLabel.optLabel {
    font-size: 13.5px;
    font-weight: 500;
    color: #16181d;
}

/* Toggle Switches (.sw) via QCheckBox */
QCheckBox {
    background-color: transparent;
    border: none;
    color: #16181d;
    font-size: 13px;
    font-weight: 500;
    spacing: 10px;
}

QCheckBox::indicator {
    width: 46px;
    height: 28px;
    background: transparent;
}

QCheckBox::indicator:unchecked {
    image: url("__SWITCH_LIGHT_OFF__");
}

QCheckBox::indicator:checked {
    image: url("__SWITCH_LIGHT_ON__");
}

/* Output Path Pill (.out) */
QFrame.outPill {
    background-color: #eceef4;
    border-radius: 999px;
    border: none;
}

QLineEdit.outPath, QLineEdit {
    background: transparent;
    color: #16181d;
    font-size: 13px;
    border: none;
    padding-left: 10px;
}

QComboBox {
    background-color: #ffffff;
    color: #16181d;
    border-radius: 999px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
    border: none;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #16181d;
    border-radius: 16px;
    padding: 4px;
    selection-background-color: #e1e4ed;
    selection-color: #16181d;
}

/* Progress Bar (.prog) */
QProgressBar {
    background-color: #e1e4ed;
    border-radius: 7px;
    max-height: 14px;
    text-align: center;
    color: transparent;
    border: none;
}

QProgressBar::chunk {
    background-color: #3e82f7;
    border-radius: 7px;
}

QLabel.progPct {
    font-size: 14px;
    font-weight: 700;
    color: #16181d;
}

/* Offset Display Box (.off) */
QFrame.offBox, QFrame.offsetCallout {
    background-color: #eceef4;
    border-radius: 28px;
    border: none;
}

QLabel.largeOffsetDisplay {
    font-size: 42px;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #16181d;
    background: transparent;
    border: none;
}

/* Check glyph compatibility: __CHECK_GLYPH_PATH__ */
QCheckBox.checkGlyph::indicator:checked {
    image: url("__CHECK_GLYPH_PATH__");
}

/* Linear Rail Slider (.sl) */
QFrame.sliderContainer, QFrame#frameSlider {
    background: transparent;
    border: none;
}

QSlider::groove:horizontal {
    height: 12px;
    background: #e1e4ed;
    border-radius: 6px;
}

QSlider::sub-page:horizontal {
    background: #3e82f7;
    border-radius: 6px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 3px solid #3e82f7;
    width: 24px;
    height: 24px;
    margin-top: -6px;
    margin-bottom: -6px;
    border-radius: 12px;
}

/* Step Nudge Buttons (.steps) */
QPushButton.stepBtn, QPushButton.btnNudge {
    background-color: #eceef4;
    border-radius: 999px;
    padding: 10px 0;
    font-size: 13px;
    font-weight: 600;
    color: #16181d;
    border: none;
}

QPushButton.stepBtn:hover, QPushButton.btnNudge:hover {
    background-color: #e1e4ed;
}

/* Metrics Grid (.mets) */
QFrame.metBox, QFrame.metricCallout {
    background-color: #eceef4;
    border-radius: 24px;
    border: none;
}

QLabel.metVal, QLabel.monoValue {
    font-size: 20px;
    font-weight: 700;
    color: #16181d;
}

/* Note Pill (.note) */
QFrame.notePill {
    background-color: #eceef4;
    border-radius: 999px;
    border: none;
}

/* Viewport Monitor (.view) */
QFrame.viewportScreen, QFrame.viewBox {
    background-color: #0c0d10;
    border-radius: 28px;
    border: none;
}

QLabel#lblTimecodeChip, QLabel.timecodeChip, QLabel.tc {
    background-color: rgba(255, 255, 255, 0.14);
    color: #ffffff;
    border-radius: 999px;
    padding: 5px 14px;
    font-weight: 600;
    font-size: 13px;
}

/* Marker Buttons (.mk) */
QPushButton.markerBtn {
    background-color: #eceef4;
    border-radius: 999px;
    padding: 12px 0;
    font-weight: 600;
    color: #6a7080;
    font-size: 13px;
    border: none;
}

QPushButton.markerBtn:hover {
    background-color: #e1e4ed;
    color: #16181d;
}

QPushButton.markerBtn:checked, QPushButton.markerBtn.on {
    background-color: #3e82f7;
    color: #ffffff;
}

/* Floating Dock (.dock) */
QFrame.floatingDock, QFrame#floatingDock, QFrame#eventLogDrawer {
    background-color: #ffffff;
    border-radius: 34px;
    border: none;
}

QLabel.logTitle {
    font-size: 14px;
    font-weight: 700;
    color: #16181d;
}

QPlainTextEdit {
    background-color: #ffffff;
    color: #6a7080;
    border: none;
    border-radius: 18px;
    font-size: 13px;
    padding: 8px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #e1e4ed;
    min-height: 24px;
    border-radius: 999px;
}

QScrollBar::handle:vertical:hover {
    background: #dcdfe8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* Empty Drop Zone */
QFrame#dropFrameEmpty {
    border: 2px dashed #e1e4ed;
    border-radius: 32px;
    background-color: #ffffff;
}

QFrame#dropFrameEmpty[dragOver="true"] {
    border: 2px dashed #3e82f7;
    background-color: #eceef4;
}

QFrame#dropFrameSingle {
    border: 1px solid #e1e4ed;
    border-radius: 32px;
    background-color: #ffffff;
}
"""

DARK_THEME_QSS = DARK_THEME_QSS.replace("__SWITCH_DARK_OFF__", get_switch_icon_path(False, "dark"))
DARK_THEME_QSS = DARK_THEME_QSS.replace("__SWITCH_DARK_ON__", get_switch_icon_path(True, "dark"))
DARK_THEME_QSS = DARK_THEME_QSS.replace("__CHECK_GLYPH_PATH__", get_check_icon_path())

LIGHT_THEME_QSS = LIGHT_THEME_QSS.replace("__SWITCH_LIGHT_OFF__", get_switch_icon_path(False, "light"))
LIGHT_THEME_QSS = LIGHT_THEME_QSS.replace("__SWITCH_LIGHT_ON__", get_switch_icon_path(True, "light"))
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
    """Applies the precision bench theme to the target application or widget."""
    widget.setStyleSheet(get_theme_stylesheet(mode))


def apply_theme(target_widget, mode: Literal["dark", "light"] = "dark"):
    """Backwards-compatible alias for apply_workbench_theme."""
    apply_workbench_theme(target_widget, mode)


def apply_one_ui_monochrome_theme(app_instance: Optional[QApplication], mode: Literal["dark", "light"] = "dark") -> None:
    """Applies the One UI theme to the application instance."""
    if app_instance is not None:
        app_instance.setStyleSheet(get_theme_stylesheet(mode))


def get_telemetry_badge_style(mode: Literal["dark", "light"] = "dark") -> str:
    """Returns CSS styles for telemetry callouts and contrast badges."""
    return "border-radius: 22px; padding: 6px 12px;"


def get_player_viewport_style(mode: Literal["dark", "light"] = "dark") -> str:
    """Returns CSS styles for the preview monitor and lip-sync player controls."""
    return "border-radius: 28px;"


def get_clean_badge_style(radius: int = 999, bg: str = "#26272d", border: str = "#2d2f36") -> str:
    """Returns CSS properties for clean, high-density micro-badges with smooth border-radius."""
    return f"background-color: {bg}; border-radius: {radius}px; padding: 3px 12px;"


def get_telemetry_display_style(is_accent: bool = False) -> str:
    """Returns CSS properties for precision telemetry boxes with rounded corners."""
    return "border-radius: 999px; padding: 4px 14px; font-weight: 700;"


def get_topbar_brand_style() -> str:
    """Returns CSS styling for the topbar branding block."""
    return "background-color: transparent;"


def get_role_badge_style(role_type: str) -> str:
    """Returns CSS/QSS styling string for stream role classification badges."""
    return "border-radius: 999px; padding: 2px 12px; font-size: 12px; font-weight: 600;"


def get_action_chip_style(action_type: str) -> str:
    """Returns CSS/QSS styling string for stream action/state chips (Copy, Align)."""
    return "border-radius: 999px; padding: 4px 14px; font-size: 12px; font-weight: 700; min-width: 64px;"
