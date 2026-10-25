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


def get_switch_icon_path(is_on: bool, mode: Literal["dark", "light"] = "dark", force_regen: bool = False) -> str:
    """Generates crisp One UI rounded toggle switch capsule assets in neutral monochrome."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    filename = f"switch_{mode}_{'on' if is_on else 'off'}.png"
    filepath = os.path.join(ASSETS_DIR, filename)
    if force_regen or not os.path.isfile(filepath):
        try:
            from PySide6.QtGui import QImage, QPainter, QColor, QBrush
            from PySide6.QtCore import Qt, QRectF
            img = QImage(46, 28, QImage.Format_ARGB32)
            img.fill(Qt.transparent)
            painter = QPainter(img)
            painter.setRenderHint(QPainter.Antialiasing, True)

            # Capsule background
            if is_on:
                bg_col = QColor("#ffffff" if mode == "dark" else "#16181d")
                thumb_col = QColor("#1b1c20" if mode == "dark" else "#ffffff")
            else:
                bg_col = QColor("#33343b" if mode == "dark" else "#e1e4ed")
                thumb_col = QColor("#9a9eac" if mode == "dark" else "#ffffff")

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(bg_col))
            painter.drawRoundedRect(QRectF(0, 0, 46, 28), 14, 14)

            # Thumb circle
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
            "accent": "#ffffff",
            "accent_soft": "#33343b",
            "accent_text": "#000000",
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
        "accent": "#16181d",
        "accent_soft": "#dcdfe8",
        "accent_text": "#ffffff",
        "ok": "#2fb16b",
        "warn": "#e8963a",
        "border_subtle": "#dcdfe8",
    }


# ==============================================================================
# Dark Theme QSS (One UI 8.5: #000000 base, #1b1c20 cards, #ffffff accent)
# Compatibility tokens: #0a0b0d, #111317, #eef0f2

# ==============================================================================
DARK_THEME_QSS = """
/* Compatibility tokens: #0a0b0d, #111317, #eef0f2, border-radius: 999px */

/* Global Window & Typography (One UI 8.5 Dark) */
QWidget {
    background-color: #000000;
    color: #f2f3f7;
    font-family: 'Figtree', 'Inter', 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    selection-background-color: #33343b;
    selection-color: #f2f3f7;
}

QFrame {
    border-radius: 24px;
}

QDialog, QMessageBox, QDialog#completionDialog {
    background-color: #1b1c20;
    color: #f2f3f7;
    border-radius: 28px;
    border: 1px solid #33343b;
}

QToolTip {
    background-color: #1b1c20;
    color: #f2f3f7;
    border: 1px solid #33343b;
    border-radius: 12px;
    padding: 6px 12px;
    font-size: 12px;
}

QMenu {
    background-color: #1b1c20;
    color: #f2f3f7;
    border: 1px solid #33343b;
    border-radius: 18px;
    padding: 6px;
}

QMenu::item {
    border-radius: 10px;
    padding: 6px 16px;
}

QMenu::item:selected {
    background-color: #26272d;
    border-radius: 10px;
}

QLabel {
    background-color: transparent;
    border: none;
}

QScrollArea {
    background-color: transparent;
    border: none;
    border-radius: 24px;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

QStackedWidget {
    background-color: transparent;
    border: none;
    border-radius: 24px;
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
QFrame#pillWorkspace, QFrame.pill, QLabel.pill, QPushButton.pill, QPushButton#btnTheme, QPushButton#btnCheckUpdates, QPushButton#btnResetOffset, QPushButton#btn_reset {
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    background-color: #1b1c20;
    color: #f2f3f7;
    padding: 0 14px;
    font-weight: 600;
    font-size: 13px;
    border: none;
}

QFrame#pillWorkspace {
    padding: 0px;
}

QFrame#pillWorkspace:hover, QFrame.pill:hover, QPushButton.pill:hover, QPushButton#btnTheme:hover, QPushButton#btnCheckUpdates:hover, QPushButton#btnResetOffset:hover, QPushButton#btn_reset:hover {
    background-color: #26272d;
    border-radius: 17px;
}

QFrame#pillWorkspace:pressed, QFrame.pill:pressed, QPushButton.pill:pressed, QPushButton#btnTheme:pressed, QPushButton#btnCheckUpdates:pressed, QPushButton#btnResetOffset:pressed, QPushButton#btn_reset:pressed {
    background-color: #33343b;
    border-radius: 17px;
}

QFrame.pillSoft {
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    background-color: #26272d;
    color: #9a9eac;
    padding: 0 14px;
    border: none;
}

QLabel.pillSoft, QLabel#badgeBackendMpv, QLabel#badgeVersion {
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    background-color: #26272d;
    color: #9a9eac;
    padding: 0 14px;
    font-weight: 600;
    font-size: 13px;
    border: none;
    qproperty-alignment: AlignCenter;
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
QLabel.tag, QLabel#badgeVFmt, QLabel#badgeAFmt, QLabel.formatChip, QLabel.statusPill, QLabel#chipFFT, QLabel#chipTrack {
    border-radius: 999px;
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #33343b;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 700;
}

QLabel.tagNeutral, QLabel.tagN, QLabel.badgeNeutral, QLabel.codecChip, QLabel.systemChip {
    border-radius: 999px;
    background-color: #26272d;
    color: #9a9eac;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 600;
}

QLabel.tagGreen, QLabel.tagG, QLabel.badgeGreen, QLabel.badgeSignal {
    border-radius: 999px;
    background-color: rgba(47, 177, 107, 0.16);
    color: #2fb16b;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 700;
}

QLabel.tagWarn, QLabel.badgeAmber {
    border-radius: 999px;
    background-color: rgba(232, 150, 58, 0.16);
    color: #e8963a;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 700;
}

QLabel.badgeRecommended, QLabel#badgeRecommended {
    border-radius: 999px;
    background-color: #33343b;
    color: #ffffff;
    border: 1px solid #50535e;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 700;
}

/* Buttons (One UI Continuous Pills) */
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
    border-radius: 999px;
}

QPushButton.btn:pressed {
    background-color: #40424c;
    border-radius: 999px;
}

QPushButton.btnPrimary, QPushButton.btnPr, QPushButton.btnSuccess {
    border-radius: 999px;
    background-color: #ffffff;
    color: #000000;
    padding: 12px 26px;
    font-weight: 700;
    font-size: 15px;
    border: none;
}

QPushButton.btnPrimary:hover, QPushButton.btnSuccess:hover {
    background-color: #e5e5e5;
    border-radius: 999px;
}

QPushButton.btnPrimary:pressed, QPushButton.btnSuccess:pressed {
    background-color: #cccccc;
    border-radius: 999px;
}

QPushButton.btnPrimary:disabled, QPushButton.btnSuccess:disabled {
    background-color: #33343b;
    color: #6a7080;
    border-radius: 999px;
}

QPushButton.btnSm, QPushButton.btnSecondary, QPushButton.btnDanger, QPushButton#btnRestore, QPushButton.btnRestore, QPushButton#btn_restore, QPushButton#btnBrowse, QPushButton#btnStopPreview {
    border-radius: 999px;
    background-color: #26272d;
    color: #f2f3f7;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 600;
    border: none;
}

QPushButton.btnSm:hover, QPushButton.btnSecondary:hover, QPushButton#btnRestore:hover, QPushButton.btnRestore:hover, QPushButton#btn_restore:hover, QPushButton#btnBrowse:hover, QPushButton#btnStopPreview:hover {
    background-color: #33343b;
    border-radius: 999px;
}

QPushButton.btnSm:pressed, QPushButton.btnSecondary:pressed, QPushButton#btnRestore:pressed, QPushButton.btnRestore:pressed, QPushButton#btn_restore:pressed, QPushButton#btnBrowse:pressed, QPushButton#btnStopPreview:pressed {
    background-color: #40424c;
    border-radius: 999px;
}

QPushButton.btnSm:disabled, QPushButton.btnSecondary:disabled, QPushButton#btnRestore:disabled, QPushButton#btnBrowse:disabled, QPushButton#btnStopPreview:disabled, QPushButton.pill:disabled, QPushButton#btnTheme:disabled, QPushButton#btnCheckUpdates:disabled, QPushButton#btnResetOffset:disabled, QPushButton#btn_reset:disabled, QPushButton:disabled {
    background-color: #1b1c20;
    color: #555864;
    border-radius: 999px;
    border: none;
}

/* File Box (Pair Grid) */
QFrame.fileBox, QFrame.fileCardWorkbench, QFrame.subCard, QFrame#cardFileV, QFrame#cardFileA {
    background-color: #26272d;
    border-radius: 20px;
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
    background-color: #26272d;
    border-radius: 24px;
    border: 1px solid #33343b;
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
    border: 2px solid #50535e;
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
    background-color: #ffffff;
    color: #000000;
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
    border-radius: 14px;
    background-color: #1b1c20;
    color: #f2f3f7;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
}

QLabel.streamActionChip {
    border-radius: 14px;
    background-color: #33343b;
    color: #ffffff;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 700;
    min-width: 64px;
}

/* Audit Pill Row (.audit) */
QFrame.auditPill, QFrame#frameAudioAudit {
    background-color: #26272d;
    border-radius: 22px;
    border: none;
}

/* Option Pill Rows (.opt) */
QFrame.optRow, QFrame.optionsContainer, QFrame#frameOptions {
    background-color: #26272d;
    border-radius: 22px;
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
    border-radius: 14px;
    background: transparent;
}

QCheckBox::indicator:unchecked {
    image: url("__SWITCH_DARK_OFF__");
}

QCheckBox::indicator:checked {
    image: url("__SWITCH_DARK_ON__");
}

/* Output Path Pill (.out) */
QFrame.outPill, QFrame#frameOutPath {
    background-color: #26272d;
    border-radius: 999px;
    border: none;
}

QLineEdit.outPath, QLineEdit#txtOutputPath, QLineEdit, QLineEdit#outputBoxMonospace {
    background-color: #26272d;
    color: #f2f3f7;
    font-size: 13px;
    border: 1px solid #33343b;
    padding: 6px 16px;
    border-radius: 999px;
}

QLineEdit:focus, QLineEdit#txtOutputPath:focus, QLineEdit#outputBoxMonospace:focus {
    border: 1px solid #50535e;
    border-radius: 999px;
}

QComboBox {
    background-color: #1b1c20;
    color: #f2f3f7;
    border-radius: 999px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #33343b;
}

QComboBox:hover {
    background-color: #26272d;
    border-radius: 999px;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #1b1c20;
    color: #f2f3f7;
    border: 1px solid #33343b;
    border-radius: 16px;
    padding: 6px;
    selection-background-color: #33343b;
    selection-color: #f2f3f7;
    outline: none;
}

QComboBox QAbstractItemView::item {
    border-radius: 10px;
    padding: 6px 12px;
    min-height: 28px;
}

QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected {
    background-color: #33343b;
    border-radius: 10px;
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
    background-color: #ffffff;
    border-radius: 7px;
}

QLabel.progPct {
    font-size: 14px;
    font-weight: 700;
    color: #f2f3f7;
}

/* Stepper Granularity Control */
QFrame#stepperGroup {
    background-color: #1b1c20;
    border-radius: 999px;
    border: 1px solid #33343b;
}

QFrame#stepperGroup QPushButton {
    background-color: transparent;
    color: #9a9eac;
    border-radius: 999px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
    border: none;
}

QFrame#stepperGroup QPushButton:hover {
    background-color: #26272d;
    color: #f2f3f7;
}

QFrame#stepperGroup QPushButton[active="true"] {
    background-color: #ffffff;
    color: #000000;
    font-weight: 700;
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

/* Sensitivity Stepper Pill Group */
QFrame#sensitivitySelector, QFrame#stepperGroup {
    background-color: #26272d;
    border-radius: 999px;
    border: 1px solid #33343b;
    padding: 2px;
}

QPushButton.pillSegmentBtn {
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    padding: 3px 12px;
    border: none;
    background-color: transparent;
    color: #9a9eac;
}

QPushButton.pillSegmentBtn:hover {
    background-color: #33343b;
    color: #f2f3f7;
    border-radius: 999px;
}

/* Linear Rail Slider (.sl) */
QFrame.sliderContainer, QFrame#frameSlider {
    background-color: #26272d;
    border-radius: 20px;
    border: 1px solid #33343b;
}

QSlider {
    background: transparent;
    border: none;
}

QSlider:focus {
    border: none;
    outline: none;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #33343b;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    height: 6px;
    background: #50535e;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: none;
    width: 18px;
    height: 18px;
    margin-top: -6px;
    margin-bottom: -6px;
    border-radius: 9px;
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
    border-radius: 999px;
}

/* Metrics Grid (.mets) */
QFrame.metBox, QFrame.metricCallout {
    background-color: #26272d;
    border-radius: 22px;
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
    border-radius: 20px;
    border: none;
}

/* Viewport Monitor (.view) */
QFrame.viewportScreen, QFrame.viewBox {
    background-color: #0c0d10;
    border-radius: 24px;
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

QProgressBar#playbackBar {
    background-color: rgba(255, 255, 255, 0.18);
    border-radius: 3px;
    border: none;
    max-height: 6px;
    height: 6px;
}

QProgressBar#playbackBar::chunk {
    background-color: #ffffff;
    border-radius: 3px;
}

QLabel#lblPlayerStatus {
    color: #aeb3c2;
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
    border-radius: 999px;
}

QPushButton.markerBtn:checked, QPushButton.markerBtn.on, QPushButton.markerBtn[on="true"] {
    background-color: #ffffff;
    color: #000000;
    border-radius: 999px;
}

/* Floating Dock (.dock) */
QFrame.floatingDock, QFrame#floatingDock, QFrame#eventLogDrawer {
    background-color: #1b1c20;
    border-radius: 34px;
    border: none;
}

QFrame.floatingDock QPushButton, QFrame#floatingDock QPushButton, QFrame#eventLogDrawer QPushButton {
    border-radius: 999px;
}

QLabel.logTitle {
    font-size: 14px;
    font-weight: 700;
    color: #f2f3f7;
}

QPlainTextEdit {
    background-color: #1b1c20;
    color: #9a9eac;
    border: 1px solid #26272d;
    border-radius: 20px;
    font-size: 13px;
    padding: 10px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #33343b;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #40424c;
    border-radius: 4px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    background: transparent;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #33343b;
    min-width: 24px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #40424c;
    border-radius: 4px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
    background: transparent;
}

/* Unified & Empty Drop Zone */
UnifiedDropZone, QFrame#unifiedDropZone {
    background: transparent;
    border: none;
    border-radius: 24px;
}

QFrame#dropFrameEmpty {
    border: 2px dashed #33343b;
    border-radius: 24px;
    background-color: #1b1c20;
}

QFrame#dropFrameEmpty[dragOver="true"] {
    border: 2px dashed #ffffff;
    background-color: #26272d;
}

QFrame#dropFrameSingle {
    border: 1px solid #33343b;
    border-radius: 24px;
    background-color: #1b1c20;
}

/* Additional Rounded Components */
QDoubleSpinBox, QSpinBox {
    background-color: #1b1c20;
    color: #f2f3f7;
    border: 1px solid #33343b;
    border-radius: 999px;
    padding: 4px 12px;
}

QGroupBox {
    border: 1px solid #33343b;
    border-radius: 20px;
    padding-top: 14px;
}

QAbstractScrollArea {
    border-radius: 20px;
}

QLabel#badgeSuccessGlyph {
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
    border-radius: 18px;
    background-color: rgba(47, 177, 107, 0.16);
    color: #2fb16b;
    font-weight: 700;
    font-size: 14px;
    qproperty-alignment: AlignCenter;
}

QPushButton#collapsibleHeaderBtn, QPushButton.collapsibleBtn {
    border-radius: 999px;
    background-color: #26272d;
    color: #f2f3f7;
    padding: 8px 18px;
    font-weight: 600;
    border: none;
}

QPushButton#collapsibleHeaderBtn:hover, QPushButton.collapsibleBtn:hover {
    background-color: #33343b;
    border-radius: 999px;
}
"""

# ==============================================================================
# Light Theme QSS (One UI 8.5: #f1f2f6 base, #ffffff cards, #16181d accent)
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

QFrame {
    border-radius: 24px;
}

QDialog, QMessageBox, QDialog#completionDialog {
    background-color: #ffffff;
    color: #16181d;
    border-radius: 28px;
    border: 1px solid #dcdfe8;
}

QToolTip {
    background-color: #ffffff;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 12px;
    padding: 6px 12px;
    font-size: 12px;
}

QMenu {
    background-color: #ffffff;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 18px;
    padding: 6px;
}

QMenu::item {
    border-radius: 10px;
    padding: 6px 16px;
}

QMenu::item:selected {
    background-color: #eceef4;
    border-radius: 10px;
}

QLabel {
    background-color: transparent;
    border: none;
}

QScrollArea {
    background-color: transparent;
    border: none;
    border-radius: 24px;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

QStackedWidget {
    background-color: transparent;
    border: none;
    border-radius: 24px;
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
QFrame#pillWorkspace, QFrame.pill, QLabel.pill, QPushButton.pill, QPushButton#btnTheme, QPushButton#btnCheckUpdates, QPushButton#btnResetOffset, QPushButton#btn_reset {
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    background-color: #ffffff;
    color: #16181d;
    padding: 0 14px;
    font-weight: 600;
    font-size: 13px;
    border: none;
}

QFrame#pillWorkspace {
    padding: 0px;
}

QFrame#pillWorkspace:hover, QFrame.pill:hover, QPushButton.pill:hover, QPushButton#btnTheme:hover, QPushButton#btnCheckUpdates:hover, QPushButton#btnResetOffset:hover, QPushButton#btn_reset:hover {
    background-color: #eceef4;
    border-radius: 17px;
}

QFrame#pillWorkspace:pressed, QFrame.pill:pressed, QPushButton.pill:pressed, QPushButton#btnTheme:pressed, QPushButton#btnCheckUpdates:pressed, QPushButton#btnResetOffset:pressed, QPushButton#btn_reset:pressed {
    background-color: #e1e4ed;
    border-radius: 17px;
}

QFrame.pillSoft {
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    background-color: #eceef4;
    color: #6a7080;
    padding: 0 14px;
    border: none;
}

QLabel.pillSoft, QLabel#badgeBackendMpv, QLabel#badgeVersion {
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    background-color: #eceef4;
    color: #6a7080;
    padding: 0 14px;
    font-weight: 600;
    font-size: 13px;
    border: none;
    qproperty-alignment: AlignCenter;
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
QLabel.tag, QLabel#badgeVFmt, QLabel#badgeAFmt, QLabel.formatChip, QLabel.statusPill, QLabel#chipFFT, QLabel#chipTrack {
    border-radius: 999px;
    background-color: #eceef4;
    color: #16181d;
    border: 1px solid #dcdfe8;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 700;
}

QLabel.tagNeutral, QLabel.tagN, QLabel.badgeNeutral, QLabel.codecChip, QLabel.systemChip {
    border-radius: 999px;
    background-color: #eceef4;
    color: #6a7080;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 600;
}

QLabel.tagGreen, QLabel.tagG, QLabel.badgeGreen, QLabel.badgeSignal {
    border-radius: 999px;
    background-color: rgba(47, 177, 107, 0.16);
    color: #2fb16b;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 700;
}

QLabel.tagWarn, QLabel.badgeAmber {
    border-radius: 999px;
    background-color: rgba(232, 150, 58, 0.16);
    color: #e8963a;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 700;
}

QLabel.badgeRecommended, QLabel#badgeRecommended {
    border-radius: 999px;
    background-color: #e1e4ed;
    color: #16181d;
    border: 1px solid #dcdfe8;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 700;
}

/* Buttons (One UI Continuous Pills) */
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
    border-radius: 999px;
}

QPushButton.btn:pressed {
    background-color: #dcdfe8;
    border-radius: 999px;
}

QPushButton.btnPrimary, QPushButton.btnPr, QPushButton.btnSuccess {
    border-radius: 999px;
    background-color: #16181d;
    color: #ffffff;
    padding: 12px 26px;
    font-weight: 700;
    font-size: 15px;
    border: none;
}

QPushButton.btnPrimary:hover, QPushButton.btnSuccess:hover {
    background-color: #2b2e36;
    border-radius: 999px;
}

QPushButton.btnPrimary:pressed, QPushButton.btnSuccess:pressed {
    background-color: #3f424c;
    border-radius: 999px;
}

QPushButton.btnPrimary:disabled, QPushButton.btnSuccess:disabled {
    background-color: #e1e4ed;
    color: #9a9eac;
    border-radius: 999px;
}

QPushButton.btnSm, QPushButton.btnSecondary, QPushButton.btnDanger, QPushButton#btnRestore, QPushButton.btnRestore, QPushButton#btn_restore, QPushButton#btnBrowse, QPushButton#btnStopPreview {
    border-radius: 999px;
    background-color: #eceef4;
    color: #16181d;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 600;
    border: none;
}

QPushButton.btnSm:hover, QPushButton.btnSecondary:hover, QPushButton#btnRestore:hover, QPushButton.btnRestore:hover, QPushButton#btn_restore:hover, QPushButton#btnBrowse:hover, QPushButton#btnStopPreview:hover {
    background-color: #e1e4ed;
    border-radius: 999px;
}

QPushButton.btnSm:pressed, QPushButton.btnSecondary:pressed, QPushButton#btnRestore:pressed, QPushButton.btnRestore:pressed, QPushButton#btn_restore:pressed, QPushButton#btnBrowse:pressed, QPushButton#btnStopPreview:pressed {
    background-color: #dcdfe8;
    border-radius: 999px;
}

QPushButton.btnSm:disabled, QPushButton.btnSecondary:disabled, QPushButton#btnRestore:disabled, QPushButton#btnBrowse:disabled, QPushButton#btnStopPreview:disabled, QPushButton.pill:disabled, QPushButton#btnTheme:disabled, QPushButton#btnCheckUpdates:disabled, QPushButton#btnResetOffset:disabled, QPushButton#btn_reset:disabled, QPushButton:disabled {
    background-color: #eceef4;
    color: #9a9eac;
    border-radius: 999px;
    border: none;
}

/* File Box (Pair Grid) */
QFrame.fileBox, QFrame.fileCardWorkbench, QFrame.subCard, QFrame#cardFileV, QFrame#cardFileA {
    background-color: #eceef4;
    border-radius: 20px;
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
    background-color: #eceef4;
    border-radius: 24px;
    border: 1px solid #dcdfe8;
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
    border: 2px solid #16181d;
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
    background-color: #16181d;
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
    border-radius: 14px;
    background-color: #ffffff;
    color: #16181d;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
}

QLabel.streamActionChip {
    border-radius: 14px;
    background-color: #e1e4ed;
    color: #16181d;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 700;
    min-width: 64px;
}

/* Audit Pill Row (.audit) */
QFrame.auditPill, QFrame#frameAudioAudit {
    background-color: #eceef4;
    border-radius: 22px;
    border: none;
}

/* Option Pill Rows (.opt) */
QFrame.optRow, QFrame.optionsContainer, QFrame#frameOptions {
    background-color: #eceef4;
    border-radius: 22px;
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
    border-radius: 14px;
    background: transparent;
}

QCheckBox::indicator:unchecked {
    image: url("__SWITCH_LIGHT_OFF__");
}

QCheckBox::indicator:checked {
    image: url("__SWITCH_LIGHT_ON__");
}

/* Output Path Pill (.out) */
QFrame.outPill, QFrame#frameOutPath {
    background-color: #eceef4;
    border-radius: 999px;
    border: none;
}

QLineEdit.outPath, QLineEdit#txtOutputPath, QLineEdit, QLineEdit#outputBoxMonospace {
    background-color: #eceef4;
    color: #16181d;
    font-size: 13px;
    border: 1px solid #dcdfe8;
    padding: 6px 16px;
    border-radius: 999px;
}

QLineEdit:focus, QLineEdit#txtOutputPath:focus, QLineEdit#outputBoxMonospace:focus {
    border: 1px solid #16181d;
    border-radius: 999px;
}

QComboBox {
    background-color: #ffffff;
    color: #16181d;
    border-radius: 999px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #dcdfe8;
}

QComboBox:hover {
    background-color: #eceef4;
    border-radius: 999px;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 16px;
    padding: 6px;
    selection-background-color: #e1e4ed;
    selection-color: #16181d;
    outline: none;
}

QComboBox QAbstractItemView::item {
    border-radius: 10px;
    padding: 6px 12px;
    min-height: 28px;
}

QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected {
    background-color: #e1e4ed;
    border-radius: 10px;
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
    background-color: #16181d;
    border-radius: 7px;
}

QLabel.progPct {
    font-size: 14px;
    font-weight: 700;
    color: #16181d;
}

/* Stepper Granularity Control */
QFrame#stepperGroup {
    background-color: #ffffff;
    border-radius: 999px;
    border: 1px solid #dcdfe8;
}

QFrame#stepperGroup QPushButton {
    background-color: transparent;
    color: #6a7080;
    border-radius: 999px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
    border: none;
}

QFrame#stepperGroup QPushButton:hover {
    background-color: #eceef4;
    color: #16181d;
}

QFrame#stepperGroup QPushButton[active="true"] {
    background-color: #16181d;
    color: #ffffff;
    font-weight: 700;
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

/* Sensitivity Stepper Pill Group */
QFrame#sensitivitySelector, QFrame#stepperGroup {
    background-color: #eceef4;
    border-radius: 999px;
    border: 1px solid #dcdfe8;
    padding: 2px;
}

QPushButton.pillSegmentBtn {
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    padding: 3px 12px;
    border: none;
    background-color: transparent;
    color: #6a7080;
}

QPushButton.pillSegmentBtn:hover {
    background-color: #e1e4ed;
    color: #16181d;
    border-radius: 999px;
}

/* Linear Rail Slider (.sl) */
QFrame.sliderContainer, QFrame#frameSlider {
    background-color: #eceef4;
    border-radius: 20px;
    border: 1px solid #dcdfe8;
}

QSlider {
    background: transparent;
    border: none;
}

QSlider:focus {
    border: none;
    outline: none;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #e1e4ed;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    height: 6px;
    background: #b8bcc9;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: none;
    width: 18px;
    height: 18px;
    margin-top: -6px;
    margin-bottom: -6px;
    border-radius: 9px;
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
    border-radius: 999px;
}

/* Metrics Grid (.mets) */
QFrame.metBox, QFrame.metricCallout {
    background-color: #eceef4;
    border-radius: 22px;
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
    border-radius: 20px;
    border: none;
}

/* Viewport Monitor (.view) */
QFrame.viewportScreen, QFrame.viewBox {
    background-color: #eceef4;
    border-radius: 24px;
    border: 1px solid #dcdfe8;
}

QLabel#lblTimecodeChip, QLabel.timecodeChip, QLabel.tc {
    background-color: #ffffff;
    color: #16181d;
    border-radius: 999px;
    padding: 5px 14px;
    font-weight: 600;
    font-size: 13px;
}

QProgressBar#playbackBar {
    background-color: #e1e4ed;
    border-radius: 3px;
    border: none;
    max-height: 6px;
    height: 6px;
}

QProgressBar#playbackBar::chunk {
    background-color: #16181d;
    border-radius: 3px;
}

QLabel#lblPlayerStatus {
    color: #6a7080;
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
    border-radius: 999px;
}

QPushButton.markerBtn:checked, QPushButton.markerBtn.on, QPushButton.markerBtn[on="true"] {
    background-color: #16181d;
    color: #ffffff;
    border-radius: 999px;
}

/* Floating Dock (.dock) */
QFrame.floatingDock, QFrame#floatingDock, QFrame#eventLogDrawer {
    background-color: #ffffff;
    border-radius: 34px;
    border: none;
}

QFrame.floatingDock QPushButton, QFrame#floatingDock QPushButton, QFrame#eventLogDrawer QPushButton {
    border-radius: 999px;
}

QLabel.logTitle {
    font-size: 14px;
    font-weight: 700;
    color: #16181d;
}

QPlainTextEdit {
    background-color: #ffffff;
    color: #6a7080;
    border: 1px solid #dcdfe8;
    border-radius: 20px;
    font-size: 13px;
    padding: 10px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #e1e4ed;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #dcdfe8;
    border-radius: 4px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    background: transparent;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #e1e4ed;
    min-width: 24px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #dcdfe8;
    border-radius: 4px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
    background: transparent;
}

/* Unified & Empty Drop Zone */
UnifiedDropZone, QFrame#unifiedDropZone {
    background: transparent;
    border: none;
    border-radius: 24px;
}

QFrame#dropFrameEmpty {
    border: 2px dashed #dcdfe8;
    border-radius: 24px;
    background-color: #ffffff;
}

QFrame#dropFrameEmpty[dragOver="true"] {
    border: 2px dashed #16181d;
    background-color: #eceef4;
}

QFrame#dropFrameSingle {
    border: 1px solid #dcdfe8;
    border-radius: 24px;
    background-color: #ffffff;
}

/* Additional Rounded Components */
QDoubleSpinBox, QSpinBox {
    background-color: #ffffff;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 999px;
    padding: 4px 12px;
}

QGroupBox {
    border: 1px solid #dcdfe8;
    border-radius: 20px;
    padding-top: 14px;
}

QAbstractScrollArea {
    border-radius: 20px;
}

QLabel#badgeSuccessGlyph {
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
    border-radius: 18px;
    background-color: rgba(47, 177, 107, 0.16);
    color: #2fb16b;
    font-weight: 700;
    font-size: 14px;
    qproperty-alignment: AlignCenter;
}

QPushButton#collapsibleHeaderBtn, QPushButton.collapsibleBtn {
    border-radius: 999px;
    background-color: #eceef4;
    color: #16181d;
    padding: 8px 18px;
    font-weight: 600;
    border: none;
}

QPushButton#collapsibleHeaderBtn:hover, QPushButton.collapsibleBtn:hover {
    background-color: #e1e4ed;
    border-radius: 999px;
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


def get_clean_badge_style(radius: int = 14, bg: str = "#26272d", border: str = "#2d2f36") -> str:
    """Returns CSS properties for clean, high-density micro-badges with smooth border-radius."""
    return f"background-color: {bg}; border-radius: {radius}px; padding: 3px 12px;"


def get_telemetry_display_style(is_accent: bool = False) -> str:
    """Returns CSS properties for precision telemetry boxes with rounded corners."""
    return "border-radius: 14px; padding: 4px 14px; font-weight: 700;"


def get_topbar_brand_style() -> str:
    """Returns CSS styling for the topbar branding block."""
    return "background-color: transparent;"


def get_role_badge_style(role_type: str) -> str:
    """Returns CSS/QSS styling string for stream role classification badges."""
    return "border-radius: 14px; padding: 2px 12px; font-size: 12px; font-weight: 600;"


def get_action_chip_style(action_type: str) -> str:
    """Returns CSS/QSS styling string for stream action/state chips (Copy, Align)."""
    return "border-radius: 14px; padding: 4px 14px; font-size: 12px; font-weight: 700; min-width: 64px;"


def get_pill_button_style(is_primary: bool = False, mode: Literal["dark", "light"] = "dark") -> str:
    """Returns CSS/QSS styling string for pill-shaped buttons."""
    if is_primary:
        bg = "#ffffff" if mode == "dark" else "#16181d"
        fg = "#000000" if mode == "dark" else "#ffffff"
        return f"border-radius: 999px; background-color: {bg}; color: {fg}; font-weight: 700; padding: 12px 26px; border: none;"
    bg = "#26272d" if mode == "dark" else "#eceef4"
    fg = "#f2f3f7" if mode == "dark" else "#16181d"
    return f"border-radius: 999px; background-color: {bg}; color: {fg}; font-weight: 600; padding: 10px 18px; border: none;"


def get_compact_dropzone_style(is_dragover: bool = False, mode: Literal["dark", "light"] = "dark") -> str:
    """Returns CSS/QSS styling string for the compact unified dropzone."""
    if mode == "dark":
        border_col = "#ffffff" if is_dragover else "#33343b"
        bg_col = "#26272d" if is_dragover else "#1b1c20"
    else:
        border_col = "#16181d" if is_dragover else "#dcdfe8"
        bg_col = "#eceef4" if is_dragover else "#ffffff"
    return f"border: 2px dashed {border_col}; border-radius: 24px; background-color: {bg_col};"


def get_telemetry_card_style(mode: Literal["dark", "light"] = "dark") -> str:
    """Returns CSS/QSS styling string for telemetry cards."""
    bg_col = "#26272d" if mode == "dark" else "#eceef4"
    return f"background-color: {bg_col}; border-radius: 22px; border: none;"


class StyleEngine:
    """Central styling engine enforcing continuous rounded geometry tokens across themes."""

    @staticmethod
    def apply_universal_rounded_tokens(theme_mode: Literal["dark", "light"] = "dark") -> str:
        """Returns the compiled stylesheet with universal rounded geometry tokens applied."""
        return get_theme_stylesheet(theme_mode)


def apply_universal_rounded_tokens(theme_mode: Literal["dark", "light"] = "dark") -> str:
    """Convenience functional interface for StyleEngine.apply_universal_rounded_tokens."""
    return StyleEngine.apply_universal_rounded_tokens(theme_mode)


class CustomStyleEngine(StyleEngine):
    """Specialized engine enforcing universal continuous pill and rounded token geometry."""

    @staticmethod
    def enforce_universal_pill_radius(theme_mode: Literal["dark", "light"] = "dark") -> str:
        """Returns QSS stylesheet rules strictly enforcing border-radius: 999px on all pill components."""
        return StyleEngine.apply_universal_rounded_tokens(theme_mode)


def enforce_universal_pill_radius(theme_mode: Literal["dark", "light"] = "dark") -> str:
    """Convenience functional interface for CustomStyleEngine.enforce_universal_pill_radius."""
    return CustomStyleEngine.enforce_universal_pill_radius(theme_mode)


