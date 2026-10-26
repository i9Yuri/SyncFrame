"""One UI 8.5 presentation styling for SyncFrame desktop workbench."""

import os
from typing import Dict, Literal, Optional
from PySide6.QtWidgets import QApplication

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
CHECK_GLYPH_PATH = os.path.join(ASSETS_DIR, "check_glyph.png")
ICON_SUN_PATH = os.path.join(ASSETS_DIR, "icon_sun.svg")
ICON_MOON_PATH = os.path.join(ASSETS_DIR, "icon_moon.svg")

SUN_SVG_CONTENT = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f2f3f7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="4.5"/>
  <line x1="12" y1="1" x2="12" y2="3.5"/>
  <line x1="12" y1="20.5" x2="12" y2="23"/>
  <line x1="1" y1="12" x2="3.5" y2="12"/>
  <line x1="20.5" y1="12" x2="23" y2="12"/>
  <line x1="4.22" y1="4.22" x2="5.99" y2="5.99"/>
  <line x1="18.01" y1="18.01" x2="19.78" y2="19.78"/>
  <line x1="4.22" y1="19.78" x2="5.99" y2="18.01"/>
  <line x1="18.01" y1="5.99" x2="19.78" y2="4.22"/>
</svg>"""

MOON_SVG_CONTENT = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#16181d" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
</svg>"""


def get_sun_icon_path() -> str:
    """Returns the absolute file path to the sun SVG asset, generating if missing."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    if not os.path.isfile(ICON_SUN_PATH):
        try:
            with open(ICON_SUN_PATH, "w", encoding="utf-8") as f:
                f.write(SUN_SVG_CONTENT)
        except Exception:
            pass
    return ICON_SUN_PATH.replace("\\", "/")


def get_moon_icon_path() -> str:
    """Returns the absolute file path to the moon SVG asset, generating if missing."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    if not os.path.isfile(ICON_MOON_PATH):
        try:
            with open(ICON_MOON_PATH, "w", encoding="utf-8") as f:
                f.write(MOON_SVG_CONTENT)
        except Exception:
            pass
    return ICON_MOON_PATH.replace("\\", "/")


def get_theme_icon(theme_mode: Literal["dark", "light"]):
    """Returns the QIcon for the theme toggle button: sun when dark (to activate light), moon when light (to activate dark)."""
    from PySide6.QtGui import QIcon
    if theme_mode == "dark":
        return QIcon(get_sun_icon_path())
    return QIcon(get_moon_icon_path())


ICON_TERMINAL_PATH = os.path.join(ASSETS_DIR, "icon_terminal.svg")
ICON_UPDATE_PATH = os.path.join(ASSETS_DIR, "icon_update.svg")
ICON_INFO_PATH = os.path.join(ASSETS_DIR, "icon_info.svg")

TERMINAL_SVG_CONTENT = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="4 17 10 11 4 5"/>
  <line x1="12" y1="19" x2="20" y2="19"/>
</svg>"""

UPDATE_SVG_CONTENT = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
  <path d="M3 3v5h5"/>
  <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
  <path d="M16 21h5v-5"/>
</svg>"""

INFO_SVG_CONTENT = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/>
  <line x1="12" y1="16" x2="12" y2="12"/>
  <line x1="12" y1="8" x2="12.01" y2="8"/>
</svg>"""


def get_dock_svg_path(name: str, mode: Literal["dark", "light"] = "dark") -> str:
    """Returns absolute file path to a monochrome dock tool SVG, generating dynamically if needed."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    color = "#f2f3f7" if mode == "dark" else "#16181d"
    filename = f"dock_{name}_{mode}.svg"
    filepath = os.path.join(ASSETS_DIR, filename)
    if not os.path.isfile(filepath):
        if name in ("theme", "theme_toggle"):
            # When dark: show sun with stroke #f2f3f7 (action is to switch to light)
            # When light: show moon with stroke #16181d (action is to switch to dark)
            template = (
                SUN_SVG_CONTENT.replace("#f2f3f7", color) if mode == "dark"
                else MOON_SVG_CONTENT.replace("#16181d", color)
            )
        elif name == "terminal":
            template = TERMINAL_SVG_CONTENT.replace("{color}", color)
        elif name == "update":
            template = UPDATE_SVG_CONTENT.replace("{color}", color)
        else:
            template = INFO_SVG_CONTENT.replace("{color}", color)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(template)
        except Exception:
            pass
    return filepath.replace("\\", "/")


def get_dock_icon(item_id: str, mode: Literal["dark", "light"] = "dark"):
    """Returns a QIcon corresponding to the dock item."""
    from PySide6.QtGui import QIcon
    mapping = {
        "event_log": "terminal",
        "terminal": "terminal",
        "check_updates": "update",
        "update": "update",
        "version_info": "info",
        "info": "info",
        "theme_toggle": "theme",
        "theme": "theme",
    }
    icon_name = mapping.get(item_id, "info")
    path = get_dock_svg_path(icon_name, mode)
    return QIcon(path)



def get_check_icon_path() -> str:
    """Returns the absolute file path to the checkmark glyph icon, generating it if needed."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    try:
        from PySide6.QtGui import QImage, QPainter, QColor, QPen
        from PySide6.QtCore import Qt, QPoint
        img = QImage(18, 18, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(QColor(255, 255, 255), 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
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
/* Compatibility tokens: #0a0b0d, #111317, #eef0f2, border-radius: 999px; */

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
    background-color: #121316;
    border: none;
    border-bottom: 1px solid #23252b;
}

QLabel#appTitle, QLabel#brandTitle {
    font-size: 30px;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #f2f3f7;
    line-height: 1.05;
}

QLabel#appSubtitle, QLabel#brandSubtitle {
    color: #9a9eac;
    font-size: 13px;
    font-weight: 500;
    margin-top: 2px;
}

QLabel#topCrumb {
    color: #9a9eac;
    font-size: 12px;
}

/* Header Pills (One UI Status & Actions) */
QFrame#pillWorkspace, QFrame.pill, QLabel.pill, QPushButton.pill, QPushButton#btnCheckUpdates, QPushButton#btnResetOffset, QPushButton#btn_reset {
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

QPushButton#btnTheme {
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    background-color: #1b1c20;
    color: #f2f3f7;
    padding: 0 14px;
    qproperty-iconSize: 18px 18px;
    font-size: 13px;
    font-weight: 600;
    border: none;
}

QFrame#pillWorkspace {
    padding: 0px;
}

QFrame#pillWorkspace:hover, QFrame.pill:hover, QPushButton.pill:hover, QPushButton#btnCheckUpdates:hover, QPushButton#btnResetOffset:hover, QPushButton#btn_reset:hover {
    background-color: #26272d;
    border-radius: 17px;
}

QPushButton#btnTheme:hover {
    background-color: #26272d;
    border-radius: 17px;
}

QFrame#pillWorkspace:pressed, QFrame.pill:pressed, QPushButton.pill:pressed, QPushButton#btnCheckUpdates:pressed, QPushButton#btnResetOffset:pressed, QPushButton#btn_reset:pressed {
    background-color: #33343b;
    border-radius: 17px;
}

QPushButton#btnTheme:pressed {
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
QLabel#badgeVFmt, QLabel#badgeAFmt, QLabel.formatChip {
    border-radius: 12px;
    height: 22px;
    min-height: 22px;
    max-height: 22px;
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #33343b;
    padding: 0 10px;
    font-size: 11px;
    font-weight: 700;
    qproperty-alignment: AlignCenter;
}

QWidget#badgeSoundbarAudit {
    border-radius: 12px;
    background: transparent;
}

QFrame#soundbarTooltipContainer {
    border-radius: 12px;
}

QFrame#mediaInspectorView, QFrame.inspectorCard {
    background-color: #222329;
    border-radius: 20px;
    border: 1px solid #33343b;
}

QPushButton#btnConnectiveAction {
    border: 2px dashed #33343b;
    border-radius: 22px;
    background-color: #16171b;
    color: #f2f3f7;
    font-size: 13px;
    font-weight: 700;
}

QPushButton#btnConnectiveAction:hover {
    border-color: #2fb16b;
    background-color: #1c1d22;
    color: #ffffff;
}

QPushButton#btnConnectiveAction:pressed {
    border-color: #1e7e48;
    background-color: #121316;
}

QFrame#frameSecondaryAudio {
    background-color: transparent;
    border: none;
}

QWidget#secondaryContainer,
QWidget#secondary_container {
    background: transparent;
    background-color: transparent;
    border: none;
}

QLabel#lblFsaTitle {
    color: #f2f3f7;
    font-size: 13px;
    font-weight: 700;
    background: transparent;
    border: none;
}

QLabel#chipFsaStatus {
    background-color: #222329;
    color: #2fb16b;
    border: 1px solid #2fb16b;
    border-radius: 12px;
    font-weight: 700;
    font-size: 10px;
    padding: 0 10px;
}

QCheckBox.chkSecondaryAudio,
QCheckBox[class="chkSecondaryAudio"],
QFrame#frameSecondaryAudio QCheckBox {
    color: #f2f3f7;
    font-size: 12px;
    font-weight: 600;
    spacing: 8px;
    min-height: 22px;
    background: transparent;
}

QCheckBox.chkSecondaryAudio::indicator,
QCheckBox[class="chkSecondaryAudio"]::indicator,
QFrame#frameSecondaryAudio QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 1px solid #383942;
    background-color: #1b1c20;
}

QCheckBox.chkSecondaryAudio::indicator:unchecked,
QCheckBox[class="chkSecondaryAudio"]::indicator:unchecked,
QFrame#frameSecondaryAudio QCheckBox::indicator:unchecked {
    image: none;
}

QCheckBox.chkSecondaryAudio::indicator:checked,
QCheckBox[class="chkSecondaryAudio"]::indicator:checked,
QFrame#frameSecondaryAudio QCheckBox::indicator:checked {
    background-color: #2fb16b;
    border-color: #2fb16b;
    image: url("__CHECK_GLYPH_PATH__");
}

QFrame.secondaryTrackCard,
QFrame[class="secondaryTrackCard"] {
    background: transparent;
    background-color: transparent;
    border: none;
}

QLabel.atomicChip,
QLabel[class="atomicChip"] {
    background-color: #222329;
    border-radius: 10px;
    height: 20px;
    min-height: 20px;
    max-height: 20px;
    padding: 0 8px;
    border: 1px solid #383942;
    color: #f2f3f7;
    font-size: 11px;
    font-weight: 600;
}

QLabel.atomicChipBest,
QLabel[class="atomicChipBest"] {
    background-color: #3e4452;
    border-radius: 10px;
    height: 20px;
    min-height: 20px;
    max-height: 20px;
    padding: 0 8px;
    border: 1px solid #636b7e;
    color: #ffffff;
    font-size: 10px;
    font-weight: 700;
}

QLabel#lblAuditSpecs {
    color: #f2f3f7;
    font-family: monospace;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: -0.01em;
    background: transparent;
}

QLabel.statusPill, QLabel#chipFFT, QLabel.tag {
    border-radius: 14px;
    height: 26px;
    min-height: 26px;
    max-height: 26px;
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #33343b;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 700;
    qproperty-alignment: AlignCenter;
}

QLabel#chipTrack {
    border-radius: 17px;
    height: 32px;
    min-height: 32px;
    max-height: 32px;
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #33343b;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 700;
    qproperty-alignment: AlignCenter;
}

QLabel.tagNeutral, QLabel.tagN, QLabel.badgeNeutral, QLabel.codecChip, QLabel.systemChip, QLabel#tagIngest {
    border-radius: 14px;
    height: 28px;
    min-height: 28px;
    max-height: 28px;
    background-color: #26272d;
    color: #9a9eac;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 600;
    border: none;
    qproperty-alignment: AlignCenter;
}

QLabel#chipSourcesCount {
    border-radius: 14px;
    height: 26px;
    min-height: 26px;
    max-height: 26px;
    background-color: #1b1c20;
    color: #9a9eac;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 600;
    border: 1px solid #33343b;
    qproperty-alignment: AlignCenter;
}

QLabel.tagGreen, QLabel.tagG, QLabel.badgeGreen, QLabel.badgeSignal {
    border-radius: 14px;
    height: 28px;
    min-height: 28px;
    max-height: 28px;
    background-color: rgba(47, 177, 107, 0.16);
    color: #2fb16b;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 700;
    border: none;
}

QLabel.tagWarn, QLabel.badgeAmber, QLabel#badgeWaiting {
    border-radius: 14px;
    height: 28px;
    min-height: 28px;
    max-height: 28px;
    background-color: rgba(232, 150, 58, 0.16);
    color: #e8963a;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 700;
    border: none;
}

QLabel.badgeRecommended, QLabel#badgeRecommended {
    border-radius: 14px;
    height: 28px;
    min-height: 28px;
    max-height: 28px;
    background-color: #33343b;
    color: #ffffff;
    border: 1px solid #50535e;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 700;
}

/* Buttons (One UI Continuous Pills) */
QPushButton.btn {
    border-radius: 20px;
    height: 40px;
    min-height: 40px;
    max-height: 40px;
    background-color: #26272d;
    color: #f2f3f7;
    padding: 0 18px;
    font-weight: 600;
    font-size: 13px;
    border: none;
}

QPushButton.btn:hover {
    background-color: #33343b;
    border-radius: 20px;
}

QPushButton.btn:pressed {
    background-color: #40424c;
    border-radius: 20px;
}

QPushButton.btnPrimary, QPushButton.btnPr, QPushButton.btnSuccess, QPushButton#btnBrowse, QPushButton#btnBrowseSecond, QPushButton#btnConfirm, QPushButton#btnCloseCompletion {
    border-radius: 22px;
    height: 44px;
    min-height: 44px;
    max-height: 44px;
    background-color: #ffffff;
    color: #000000;
    padding: 0 26px;
    font-weight: 700;
    font-size: 15px;
    border: none;
}

QPushButton.btnPrimary:hover, QPushButton.btnSuccess:hover, QPushButton#btnBrowse:hover, QPushButton#btnBrowseSecond:hover, QPushButton#btnConfirm:hover, QPushButton#btnCloseCompletion:hover {
    background-color: #e5e5e5;
    border-radius: 22px;
}

QPushButton.btnPrimary:pressed, QPushButton.btnSuccess:pressed, QPushButton#btnBrowse:pressed, QPushButton#btnBrowseSecond:pressed, QPushButton#btnConfirm:pressed, QPushButton#btnCloseCompletion:pressed {
    background-color: #cccccc;
    border-radius: 22px;
}

QPushButton.btnPrimary:disabled, QPushButton.btnSuccess:disabled, QPushButton#btnBrowse:disabled, QPushButton#btnBrowseSecond:disabled, QPushButton#btnConfirm:disabled, QPushButton#btnCloseCompletion:disabled {
    background-color: #33343b;
    color: #6a7080;
    border-radius: 22px;
}

QPushButton.btnSm, QPushButton.btnSecondary, QPushButton.btnDanger, QPushButton#btnRestore, QPushButton.btnRestore, QPushButton#btn_restore, QPushButton#btnStopPreview, QPushButton#btnResetSingle {
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    background-color: #26272d;
    color: #f2f3f7;
    padding: 0 14px;
    font-size: 13px;
    font-weight: 600;
    border: none;
}

QPushButton.btnSm:hover, QPushButton.btnSecondary:hover, QPushButton#btnRestore:hover, QPushButton.btnRestore:hover, QPushButton#btn_restore:hover, QPushButton#btnStopPreview:hover, QPushButton#btnResetSingle:hover {
    background-color: #33343b;
    border-radius: 17px;
}

QPushButton.btnSm:pressed, QPushButton.btnSecondary:pressed, QPushButton#btnRestore:pressed, QPushButton.btnRestore:pressed, QPushButton#btn_restore:pressed, QPushButton#btnStopPreview:pressed, QPushButton#btnResetSingle:pressed {
    background-color: #40424c;
    border-radius: 17px;
}

QPushButton.btnSm:disabled, QPushButton.btnSecondary:disabled, QPushButton#btnRestore:disabled, QPushButton#btnStopPreview:disabled, QPushButton#btnResetSingle:disabled, QPushButton.pill:disabled, QPushButton#btnTheme:disabled, QPushButton#btnCheckUpdates:disabled, QPushButton#btnResetOffset:disabled, QPushButton#btn_reset:disabled, QPushButton:disabled {
    background-color: #1b1c20;
    color: #555864;
    border-radius: 17px;
    border: none;
}

QPushButton#btnChangeFiles {
    border-radius: 14px;
    height: 26px;
    min-height: 26px;
    max-height: 26px;
    background-color: #222329;
    color: #f2f3f7;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 600;
    border: 1px solid #33343b;
}

QPushButton#btnChangeFiles:hover {
    background-color: #33343b;
    border-radius: 14px;
}

QPushButton#btnChangeFiles:pressed {
    background-color: #40424c;
    border-radius: 14px;
}

QPushButton#btnChangeFiles:disabled {
    background-color: #1b1c20;
    color: #555864;
    border-radius: 14px;
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

/* Audit Pill Row & Resulting Specs Bar (.audit, .resultingSpecsBar) */
QFrame.auditPill, QFrame.resultingSpecsBar, QFrame#frameAudioAudit {
    background-color: #1b1c20;
    border: 1px solid #282d34;
    border-radius: 20px;
    min-height: 38px;
}

QLabel.resultingTitle, QLabel#lblResultingTitle {
    color: #9a9eac;
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.02em;
    background: transparent;
    border: none;
    padding-right: 4px;
}

QLabel.resultingSpecPill, QLabel[class~="resultingSpecPill"] {
    background-color: #222329;
    border: 1px solid #32353e;
    border-radius: 12px;
    height: 24px;
    min-height: 24px;
    max-height: 24px;
    padding: 0 10px;
    font-size: 11px;
    font-weight: 600;
    color: #f2f3f7;
    qproperty-alignment: AlignCenter;
}

QLabel.resultingPillSignal, QLabel[class~="resultingPillSignal"] {
    background-color: rgba(255, 255, 255, 0.12);
    border: 1px solid #e1e4ed;
    color: #ffffff;
    font-weight: 700;
}

QLabel.resultingPillGreen, QLabel[class~="resultingPillGreen"] {
    background-color: rgba(47, 177, 107, 0.18);
    border: 1px solid #2fb16b;
    color: #3dd68c;
    font-weight: 700;
}

QLabel.resultingPillAmber, QLabel[class~="resultingPillAmber"] {
    background-color: rgba(232, 150, 58, 0.16);
    border: 1px solid #e8963a;
    color: #e8963a;
    font-weight: 700;
}

QLabel.resultingPillNeutral, QLabel[class~="resultingPillNeutral"] {
    background-color: #222329;
    border: 1px solid #32353e;
    color: #9a9eac;
}

/* Option Pill Rows (.opt) */
QFrame.optionsContainer, QFrame#frameOptions {
    background-color: transparent;
    border: none;
}

QFrame.optRow {
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
    border-radius: 22px;
    height: 44px;
    min-height: 44px;
    max-height: 44px;
    border: none;
}

QLineEdit.outPath, QLineEdit#txtOutputPath {
    background: transparent;
    border: none;
    color: #f2f3f7;
    font-size: 13px;
    padding: 0 4px;
    height: 36px;
    min-height: 36px;
    max-height: 36px;
}

QLineEdit, QLineEdit#outputBoxMonospace {
    background-color: #26272d;
    color: #f2f3f7;
    font-size: 13px;
    border: 1px solid #33343b;
    padding: 0 16px;
    height: 36px;
    min-height: 36px;
    max-height: 36px;
    border-radius: 18px;
}

QLineEdit:focus, QLineEdit#outputBoxMonospace:focus {
    border: 1px solid #50535e;
    border-radius: 18px;
}

QPushButton#btnBrowseDest {
    background-color: #ffffff;
    color: #000000;
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    padding: 0 16px;
    font-weight: 700;
    font-size: 13px;
    border: none;
}

QPushButton#btnBrowseDest:hover {
    background-color: #e5e5e5;
    border-radius: 17px;
}

QPushButton#btnBrowseDest:pressed {
    background-color: #cccccc;
    border-radius: 17px;
}

QPushButton#btnCancel {
    background-color: #26272d;
    color: #f2f3f7;
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    padding: 0 16px;
    font-size: 13px;
    font-weight: 600;
    border: none;
}

QPushButton#btnCancel:hover {
    background-color: #33343b;
    border-radius: 17px;
}

QPushButton#btnCancel:pressed {
    background-color: #40424c;
    border-radius: 17px;
}

QPushButton#btnCancel:disabled {
    background-color: #1b1c20;
    color: #555864;
    border-radius: 17px;
    border: none;
}

QComboBox {
    background-color: #1b1c20;
    color: #f2f3f7;
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    padding: 0 14px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #33343b;
}

QComboBox:hover {
    background-color: #26272d;
    border-radius: 17px;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBoxPrivateContainer,
QFrame[class="QComboBoxPrivateContainer"] {
    background-color: transparent;
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #1b1c20;
    color: #f2f3f7;
    border: 1px solid #282d34;
    border-radius: 16px;
    padding: 6px;
    selection-background-color: #26272d;
    selection-color: #ffffff;
    outline: none;
}

QComboBox QAbstractItemView::item {
    border-radius: 10px;
    padding: 6px 12px;
    min-height: 28px;
    color: #f2f3f7;
}

QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected {
    background-color: #26272d;
    color: #ffffff;
    border-radius: 10px;
}

/* Progress Bar (.prog) */
QProgressBar {
    background-color: #33343b;
    border-radius: 7px;
    height: 14px;
    min-height: 14px;
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

/* Stepper Granularity Control & Sensitivity Stepper Pill Group */
QFrame#sensitivitySelector, QFrame#stepperGroup {
    background-color: #26272d;
    border-radius: 17px;
    border: 1px solid #33343b;
    padding: 2px 4px;
    min-height: 28px;
    max-height: 34px;
}

QFrame#sensitivitySelector QPushButton,
QFrame#stepperGroup QPushButton,
QPushButton.pillSegmentBtn {
    border-radius: 13px;
    font-size: 12px;
    font-weight: 600;
    padding: 3px 12px;
    border: none;
    background-color: transparent;
    color: #9a9eac;
    min-height: 24px;
    max-height: 26px;
}

QFrame#sensitivitySelector QPushButton:hover,
QFrame#stepperGroup QPushButton:hover,
QPushButton.pillSegmentBtn:hover {
    background-color: #33343b;
    color: #f2f3f7;
    border-radius: 13px;
}

QFrame#sensitivitySelector QPushButton:pressed,
QFrame#stepperGroup QPushButton:pressed,
QPushButton.pillSegmentBtn:pressed {
    background-color: #40424c;
    color: #f2f3f7;
    border-radius: 13px;
}

QFrame#sensitivitySelector QPushButton[active="true"],
QFrame#stepperGroup QPushButton[active="true"],
QPushButton.pillSegmentBtn[active="true"] {
    background-color: #ffffff;
    color: #000000;
    font-weight: 700;
    border-radius: 13px;
}

/* Offset Display Box (.off) */
QFrame.offBox, QFrame.offsetCallout {
    background-color: #202127;
    border-radius: 20px;
    border: none;
}

QLabel.largeOffsetDisplay {
    font-size: 38px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #f2f3f7;
    background: transparent;
    border: none;
}

QPushButton#btnResetOffset, QPushButton#btn_reset {
    background-color: transparent;
    border: none;
    color: #f2f3f7;
    font-size: 13px;
    font-weight: 600;
    padding: 4px 8px;
    border-radius: 10px;
}

QPushButton#btnResetOffset:hover, QPushButton#btn_reset:hover {
    color: #4081f7;
    background-color: rgba(64, 129, 247, 0.12);
}

QPushButton#btnResetOffset:pressed, QPushButton#btn_reset:pressed {
    color: #93c5fd;
    background-color: rgba(64, 129, 247, 0.20);
}

QLabel#chipTrack, QLabel.chipTrack {
    background-color: rgba(64, 129, 247, 0.18);
    color: #60a5fa;
    border-radius: 14px;
    height: 28px;
    min-height: 28px;
    max-height: 28px;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 600;
    border: none;
    qproperty-alignment: AlignCenter;
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

QSlider {
    background: transparent;
    border: none;
    min-height: 28px;
    height: 28px;
}

QSlider:focus {
    border: none;
    outline: none;
}

QSlider::groove:horizontal {
    height: 8px;
    background: #282d34;
    border-radius: 4px;
}

QSlider::sub-page:horizontal {
    height: 8px;
    background: #4081f7;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 3px solid #4081f7;
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 10px;
}

QSlider::handle:horizontal:hover {
    border-color: #60a5fa;
}

/* Step Nudge Buttons (.steps) */
QPushButton.stepBtn, QPushButton.btnNudge {
    background-color: #202127;
    border-radius: 18px;
    padding: 0;
    font-size: 12px;
    font-weight: 700;
    color: #f2f3f7;
    border: none;
    min-height: 36px;
    height: 36px;
}

QPushButton.stepBtn:hover, QPushButton.btnNudge:hover {
    background-color: #282a32;
    border-radius: 18px;
}

QPushButton.stepBtn:pressed, QPushButton.btnNudge:pressed {
    background-color: #32353f;
    border-radius: 18px;
}

QPushButton.stepBtn:disabled, QPushButton.btnNudge:disabled {
    background-color: #18191d;
    color: #555864;
    border-radius: 18px;
}

/* Metrics Grid (.mets) */
QFrame.metBox, QFrame.metricCallout {
    background-color: #202127;
    border-radius: 18px;
    border: none;
}

QLabel.metVal, QLabel.monoValue {
    font-size: 18px;
    font-weight: 700;
    color: #f2f3f7;
}

QLabel.metVal[analyzed="false"] {
    color: #9a9eac;
}

/* Note Pill (.note) */
QFrame.notePill, QFrame#frameNote {
    background-color: #202127;
    border-radius: 18px;
    border: none;
    min-height: 36px;
    height: 36px;
}

QLabel.greenDot {
    background-color: #2fb16b;
    border-radius: 4px;
    width: 8px;
    height: 8px;
    min-width: 8px;
    max-width: 8px;
    min-height: 8px;
    max-height: 8px;
    border: none;
}

QLabel#lblDiagnosisNote {
    color: #9a9eac;
    font-size: 12px;
    font-weight: 500;
    background: transparent;
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
    border-radius: 13px;
    height: 26px;
    min-height: 26px;
    max-height: 26px;
    padding: 0 14px;
    font-weight: 600;
    font-size: 13px;
    border: none;
    qproperty-alignment: AlignCenter;
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
    border-radius: 20px;
    height: 40px;
    min-height: 40px;
    max-height: 40px;
    padding: 0 16px;
    font-weight: 600;
    color: #9a9eac;
    font-size: 13px;
    border: none;
}

QPushButton.markerBtn:hover {
    background-color: #33343b;
    color: #f2f3f7;
    border-radius: 20px;
}

QPushButton.markerBtn:checked, QPushButton.markerBtn.on, QPushButton.markerBtn[on="true"] {
    background-color: #ffffff;
    color: #000000;
    border-radius: 20px;
}

QPushButton.markerBtn:pressed {
    background-color: #40424c;
    border-radius: 20px;
}

QPushButton.markerBtn:disabled {
    background-color: #1b1c20;
    color: #555864;
    border-radius: 20px;
    border: none;
}

QPushButton#btnStopPreview:disabled {
    background-color: #222329;
    color: #555864;
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    padding: 0 14px;
    border: none;
}

/* Floating Dock (.dock) */
QFrame.floatingDock, QFrame#floatingDock, QFrame#eventLogDrawer {
    background-color: #1b1c20;
    border-radius: 28px; /* border-radius: 34px; */
    border: none;
}

QLabel#badgeEventCount, QLabel.badgeEventCount {
    border-radius: 14px;
    height: 28px;
    min-height: 28px;
    max-height: 28px;
    background-color: #26272d;
    color: #9a9eac;
    padding: 0 12px;
    font-size: 12px;
    font-weight: 600;
    border: none;
    qproperty-alignment: AlignCenter;
}

QFrame.floatingDock QPushButton, QFrame#floatingDock QPushButton, QFrame#eventLogDrawer QPushButton,
QPushButton#btnDockClear, QPushButton#btnDockToggle {
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    background-color: #26272d;
    color: #f2f3f7;
    padding: 0 14px;
    font-size: 13px;
    font-weight: 600;
    border: none;
}

QFrame.floatingDock QPushButton:hover, QFrame#floatingDock QPushButton:hover,
QPushButton#btnDockClear:hover, QPushButton#btnDockToggle:hover {
    background-color: #33343b;
    border-radius: 17px;
}

QFrame.floatingDock QPushButton:pressed, QFrame#floatingDock QPushButton:pressed,
QPushButton#btnDockClear:pressed, QPushButton#btnDockToggle:pressed {
    background-color: #40424c;
    border-radius: 17px;
}

QFrame.floatingDock QPushButton:disabled, QFrame#floatingDock QPushButton:disabled,
QPushButton#btnDockClear:disabled, QPushButton#btnDockToggle:disabled {
    background-color: #1b1c20;
    color: #555864;
    border-radius: 17px;
}

QLabel.logTitle, QLabel#dockTitle {
    font-size: 14px;
    font-weight: 700;
    color: #f2f3f7;
    background: transparent;
    border: none;
}

/* Floating Action Dock (Compact TiltedDock Nativo) */
QFrame#floatingActionDock, QFrame.floatingActionDock {
    background-color: rgba(27, 28, 32, 0.85);
    border-radius: 26px;
    border: 1px solid #26272d;
}

QPushButton#dockItemBtn, QAbstractButton.dockItemBtn {
    border-radius: 20px;
    width: 40px;
    min-width: 40px;
    max-width: 40px;
    height: 40px;
    min-height: 40px;
    max-height: 40px;
    background-color: transparent;
    border: none;
    padding: 0px;
}

QPushButton#dockItemBtn:hover, QAbstractButton.dockItemBtn:hover {
    background-color: transparent;
    border: none;
}

QPushButton#dockItemBtn:pressed, QAbstractButton.dockItemBtn:pressed {
    background-color: transparent;
    border: none;
}

QLabel#dockBadge {
    background-color: #26272d;
    color: #f2f3f7;
    border: 1px solid #33343b;
    border-radius: 8px;
    font-size: 10px;
    font-weight: 700;
    padding: 0 4px;
    min-height: 16px;
    max-height: 16px;
}

QLabel#dockTooltip {
    background-color: #111215;
    color: #f2f3f7;
    border: 1px solid #33343b;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
}

QLabel#floatingToast, QFrame#floatingToast {
    background-color: #1b1c20;
    color: #f2f3f7;
    border: 1px solid #33343b;
    border-radius: 18px;
    font-size: 12px;
    font-weight: 600;
    padding: 8px 18px;
}

QFrame#eventLogPopoverContainer, QFrame#versionInfoPopoverContainer {
    background-color: #1b1c20;
    border: 1px solid #26272d;
    border-radius: 20px;
}


QPlainTextEdit {
    background-color: #1b1c20;
    color: #9a9eac;
    border: 1px solid #26272d;
    border-radius: 20px;
    font-size: 13px;
    padding: 10px;
}

QPlainTextEdit#dockTextEdit {
    background-color: #1b1c20;
    color: #9a9eac;
    border: 1px solid #26272d;
    border-radius: 18px;
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
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    padding: 0 12px;
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
    border-radius: 18px;
    height: 36px;
    min-height: 36px;
    max-height: 36px;
    background-color: #26272d;
    color: #f2f3f7;
    padding: 0 18px;
    font-weight: 600;
    border: none;
}

QPushButton#collapsibleHeaderBtn:hover, QPushButton.collapsibleBtn:hover {
    background-color: #33343b;
    border-radius: 18px;
}
"""

# ==============================================================================
# Light Theme QSS (One UI 8.5: #f1f2f6 base, #ffffff cards, #16181d accent)
# Compatibility tokens: #f2f3f1, #191c1a, #ffffff
# ==============================================================================
LIGHT_THEME_QSS = """
/* Compatibility tokens: #f2f3f1, #191c1a, #ffffff, border-radius: 999px; */

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
    background-color: #ffffff;
    border: none;
    border-bottom: 1px solid #e1e4ed;
}

QLabel#appTitle, QLabel#brandTitle {
    font-size: 30px;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #16181d;
    line-height: 1.05;
}

QLabel#appSubtitle, QLabel#brandSubtitle {
    color: #6a7080;
    font-size: 13px;
    font-weight: 500;
    margin-top: 2px;
}

QLabel#topCrumb {
    color: #6a7080;
    font-size: 12px;
}

/* Header Pills (One UI Status & Actions) */
QFrame#pillWorkspace, QFrame.pill, QLabel.pill, QPushButton.pill, QPushButton#btnCheckUpdates, QPushButton#btnResetOffset, QPushButton#btn_reset {
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

QPushButton#btnTheme {
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    background-color: #ffffff;
    color: #16181d;
    padding: 0 14px;
    qproperty-iconSize: 18px 18px;
    font-size: 13px;
    font-weight: 600;
    border: none;
}

QFrame#pillWorkspace {
    padding: 0px;
}

QFrame#pillWorkspace:hover, QFrame.pill:hover, QPushButton.pill:hover, QPushButton#btnCheckUpdates:hover, QPushButton#btnResetOffset:hover, QPushButton#btn_reset:hover {
    background-color: #eceef4;
    border-radius: 17px;
}

QPushButton#btnTheme:hover {
    background-color: #eceef4;
    border-radius: 17px;
}

QFrame#pillWorkspace:pressed, QFrame.pill:pressed, QPushButton.pill:pressed, QPushButton#btnCheckUpdates:pressed, QPushButton#btnResetOffset:pressed, QPushButton#btn_reset:pressed {
    background-color: #e1e4ed;
    border-radius: 17px;
}

QPushButton#btnTheme:pressed {
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
QLabel#badgeVFmt, QLabel#badgeAFmt, QLabel.formatChip {
    border-radius: 12px;
    height: 22px;
    min-height: 22px;
    max-height: 22px;
    background-color: #eceef4;
    color: #16181d;
    border: 1px solid #dcdfe8;
    padding: 0 10px;
    font-size: 11px;
    font-weight: 700;
    qproperty-alignment: AlignCenter;
}

QWidget#badgeSoundbarAudit {
    border-radius: 12px;
    background: transparent;
}

QFrame#soundbarTooltipContainer {
    border-radius: 12px;
}

QFrame#mediaInspectorView, QFrame.inspectorCard {
    background-color: #eceef4;
    border-radius: 20px;
    border: 1px solid #dcdfe8;
}

QPushButton#btnConnectiveAction {
    border: 2px dashed #b8bcc8;
    border-radius: 22px;
    background-color: #f1f2f6;
    color: #16181d;
    font-size: 13px;
    font-weight: 700;
}

QPushButton#btnConnectiveAction:hover {
    border-color: #1e7e48;
    background-color: #e5e7ef;
    color: #16181d;
}

QPushButton#btnConnectiveAction:pressed {
    border-color: #145832;
    background-color: #d8dae3;
}

QFrame#frameSecondaryAudio {
    background-color: transparent;
    border: none;
}

QWidget#secondaryContainer,
QWidget#secondary_container {
    background: transparent;
    background-color: transparent;
    border: none;
}

QLabel#lblFsaTitle {
    color: #16181d;
    font-size: 13px;
    font-weight: 700;
    background: transparent;
    border: none;
}

QLabel#chipFsaStatus {
    background-color: rgba(47, 177, 107, 0.16);
    color: #2fb16b;
    border: 1px solid #2fb16b;
    border-radius: 12px;
    font-weight: 700;
    font-size: 10px;
    padding: 0 10px;
}

QCheckBox.chkSecondaryAudio,
QCheckBox[class="chkSecondaryAudio"],
QFrame#frameSecondaryAudio QCheckBox {
    color: #16181d;
    font-size: 12px;
    font-weight: 600;
    spacing: 8px;
    min-height: 22px;
    background: transparent;
}

QCheckBox.chkSecondaryAudio::indicator,
QCheckBox[class="chkSecondaryAudio"]::indicator,
QFrame#frameSecondaryAudio QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 1px solid #c2c6d4;
    background-color: #e1e4ed;
}

QCheckBox.chkSecondaryAudio::indicator:unchecked,
QCheckBox[class="chkSecondaryAudio"]::indicator:unchecked,
QFrame#frameSecondaryAudio QCheckBox::indicator:unchecked {
    image: none;
}

QCheckBox.chkSecondaryAudio::indicator:checked,
QCheckBox[class="chkSecondaryAudio"]::indicator:checked,
QFrame#frameSecondaryAudio QCheckBox::indicator:checked {
    background-color: #2fb16b;
    border-color: #2fb16b;
    image: url("__CHECK_GLYPH_PATH__");
}

QFrame.secondaryTrackCard,
QFrame[class="secondaryTrackCard"] {
    background: transparent;
    background-color: transparent;
    border: none;
}

QLabel.atomicChip,
QLabel[class="atomicChip"] {
    background-color: #e8ebf2;
    border-radius: 10px;
    height: 20px;
    min-height: 20px;
    max-height: 20px;
    padding: 0 8px;
    border: 1px solid #d0d4e0;
    color: #16181d;
    font-size: 11px;
    font-weight: 600;
}

QLabel.atomicChipBest,
QLabel[class="atomicChipBest"] {
    background-color: #d0d4e0;
    border-radius: 10px;
    height: 20px;
    min-height: 20px;
    max-height: 20px;
    padding: 0 8px;
    border: 1px solid #9ca3af;
    color: #16181d;
    font-size: 10px;
    font-weight: 700;
}

QLabel#lblAuditSpecs {
    color: #16181d;
    font-family: monospace;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: -0.01em;
    background: transparent;
}

QLabel.statusPill, QLabel#chipFFT, QLabel.tag {
    border-radius: 14px;
    height: 26px;
    min-height: 26px;
    max-height: 26px;
    background-color: #eceef4;
    color: #16181d;
    border: 1px solid #dcdfe8;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 700;
    qproperty-alignment: AlignCenter;
}

QLabel#chipTrack {
    border-radius: 17px;
    height: 32px;
    min-height: 32px;
    max-height: 32px;
    background-color: #eceef4;
    color: #16181d;
    border: 1px solid #dcdfe8;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 700;
    qproperty-alignment: AlignCenter;
}

QLabel.tagNeutral, QLabel.tagN, QLabel.badgeNeutral, QLabel.codecChip, QLabel.systemChip, QLabel#tagIngest {
    border-radius: 14px;
    height: 28px;
    min-height: 28px;
    max-height: 28px;
    background-color: #eceef4;
    color: #6a7080;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 600;
    border: none;
    qproperty-alignment: AlignCenter;
}

QLabel#chipSourcesCount {
    border-radius: 14px;
    height: 26px;
    min-height: 26px;
    max-height: 26px;
    background-color: #ffffff;
    color: #6a7080;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 600;
    border: 1px solid #dcdfe8;
    qproperty-alignment: AlignCenter;
}

QLabel.tagGreen, QLabel.tagG, QLabel.badgeGreen, QLabel.badgeSignal {
    border-radius: 14px;
    height: 28px;
    min-height: 28px;
    max-height: 28px;
    background-color: rgba(47, 177, 107, 0.16);
    color: #2fb16b;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 700;
    border: none;
}

QLabel.tagWarn, QLabel.badgeAmber, QLabel#badgeWaiting {
    border-radius: 14px;
    height: 28px;
    min-height: 28px;
    max-height: 28px;
    background-color: rgba(232, 150, 58, 0.16);
    color: #e8963a;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 700;
    border: none;
}

QLabel.badgeRecommended, QLabel#badgeRecommended {
    border-radius: 14px;
    height: 28px;
    min-height: 28px;
    max-height: 28px;
    background-color: #e1e4ed;
    color: #16181d;
    border: 1px solid #dcdfe8;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 700;
}

/* Buttons (One UI Continuous Pills) */
QPushButton.btn {
    border-radius: 20px;
    height: 40px;
    min-height: 40px;
    max-height: 40px;
    background-color: #eceef4;
    color: #16181d;
    padding: 0 18px;
    font-weight: 600;
    font-size: 13px;
    border: none;
}

QPushButton.btn:hover {
    background-color: #e1e4ed;
    border-radius: 20px;
}

QPushButton.btn:pressed {
    background-color: #dcdfe8;
    border-radius: 20px;
}

QPushButton.btnPrimary, QPushButton.btnPr, QPushButton.btnSuccess, QPushButton#btnBrowse, QPushButton#btnBrowseSecond, QPushButton#btnConfirm, QPushButton#btnCloseCompletion {
    border-radius: 22px;
    height: 44px;
    min-height: 44px;
    max-height: 44px;
    background-color: #16181d;
    color: #ffffff;
    padding: 0 26px;
    font-weight: 700;
    font-size: 15px;
    border: none;
}

QPushButton.btnPrimary:hover, QPushButton.btnSuccess:hover, QPushButton#btnBrowse:hover, QPushButton#btnBrowseSecond:hover, QPushButton#btnConfirm:hover, QPushButton#btnCloseCompletion:hover {
    background-color: #2b2e36;
    border-radius: 22px;
}

QPushButton.btnPrimary:pressed, QPushButton.btnSuccess:pressed, QPushButton#btnBrowse:pressed, QPushButton#btnBrowseSecond:pressed, QPushButton#btnConfirm:pressed, QPushButton#btnCloseCompletion:pressed {
    background-color: #3f424c;
    border-radius: 22px;
}

QPushButton.btnPrimary:disabled, QPushButton.btnSuccess:disabled, QPushButton#btnBrowse:disabled, QPushButton#btnBrowseSecond:disabled, QPushButton#btnConfirm:disabled, QPushButton#btnCloseCompletion:disabled {
    background-color: #e1e4ed;
    color: #9a9eac;
    border-radius: 22px;
}

QPushButton.btnSm, QPushButton.btnSecondary, QPushButton.btnDanger, QPushButton#btnRestore, QPushButton.btnRestore, QPushButton#btn_restore, QPushButton#btnStopPreview, QPushButton#btnResetSingle {
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    background-color: #eceef4;
    color: #16181d;
    padding: 0 14px;
    font-size: 13px;
    font-weight: 600;
    border: none;
}

QPushButton.btnSm:hover, QPushButton.btnSecondary:hover, QPushButton#btnRestore:hover, QPushButton.btnRestore:hover, QPushButton#btn_restore:hover, QPushButton#btnStopPreview:hover, QPushButton#btnResetSingle:hover {
    background-color: #e1e4ed;
    border-radius: 17px;
}

QPushButton.btnSm:pressed, QPushButton.btnSecondary:pressed, QPushButton#btnRestore:pressed, QPushButton.btnRestore:pressed, QPushButton#btn_restore:pressed, QPushButton#btnStopPreview:pressed, QPushButton#btnResetSingle:pressed {
    background-color: #dcdfe8;
    border-radius: 17px;
}

QPushButton.btnSm:disabled, QPushButton.btnSecondary:disabled, QPushButton#btnRestore:disabled, QPushButton#btnBrowse:disabled, QPushButton#btnStopPreview:disabled, QPushButton#btnResetSingle:disabled, QPushButton.pill:disabled, QPushButton#btnTheme:disabled, QPushButton#btnCheckUpdates:disabled, QPushButton#btnResetOffset:disabled, QPushButton#btn_reset:disabled, QPushButton:disabled {
    background-color: #eceef4;
    color: #9a9eac;
    border-radius: 17px;
    border: none;
}

QPushButton#btnChangeFiles {
    border-radius: 14px;
    height: 26px;
    min-height: 26px;
    max-height: 26px;
    background-color: #eceef4;
    color: #16181d;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 600;
    border: 1px solid #dcdfe8;
}

QPushButton#btnChangeFiles:hover {
    background-color: #dcdfe8;
    border-radius: 14px;
}

QPushButton#btnChangeFiles:pressed {
    background-color: #d3d6e0;
    border-radius: 14px;
}

QPushButton#btnChangeFiles:disabled {
    background-color: #f1f2f6;
    color: #9a9eac;
    border-radius: 14px;
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

/* Audit Pill Row & Resulting Specs Bar (.audit, .resultingSpecsBar) */
QFrame.auditPill, QFrame.resultingSpecsBar, QFrame#frameAudioAudit {
    background-color: #f0f2f7;
    border: 1px solid #d5d9e2;
    border-radius: 20px;
    min-height: 38px;
}

QLabel.resultingTitle, QLabel#lblResultingTitle {
    color: #555b6e;
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.02em;
    background: transparent;
    border: none;
    padding-right: 4px;
}

QLabel.resultingSpecPill, QLabel[class~="resultingSpecPill"] {
    background-color: #ffffff;
    border: 1px solid #d5d9e2;
    border-radius: 12px;
    height: 24px;
    min-height: 24px;
    max-height: 24px;
    padding: 0 10px;
    font-size: 11px;
    font-weight: 600;
    color: #16181d;
    qproperty-alignment: AlignCenter;
}

QLabel.resultingPillSignal, QLabel[class~="resultingPillSignal"] {
    background-color: rgba(22, 24, 29, 0.08);
    border: 1px solid #16181d;
    color: #16181d;
    font-weight: 700;
}

QLabel.resultingPillGreen, QLabel[class~="resultingPillGreen"] {
    background-color: rgba(30, 126, 72, 0.12);
    border: 1px solid #1e7e48;
    color: #1e7e48;
    font-weight: 700;
}

QLabel.resultingPillAmber, QLabel[class~="resultingPillAmber"] {
    background-color: rgba(180, 83, 9, 0.12);
    border: 1px solid #b45309;
    color: #b45309;
    font-weight: 700;
}

QLabel.resultingPillNeutral, QLabel[class~="resultingPillNeutral"] {
    background-color: #ffffff;
    border: 1px solid #d5d9e2;
    color: #555b6e;
}

/* Option Pill Rows (.opt) */
QFrame.optionsContainer, QFrame#frameOptions {
    background-color: transparent;
    border: none;
}

QFrame.optRow {
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
    border-radius: 22px;
    height: 44px;
    min-height: 44px;
    max-height: 44px;
    border: none;
}

QLineEdit.outPath, QLineEdit#txtOutputPath {
    background: transparent;
    border: none;
    color: #16181d;
    font-size: 13px;
    padding: 0 4px;
    height: 36px;
    min-height: 36px;
    max-height: 36px;
}

QLineEdit, QLineEdit#outputBoxMonospace {
    background-color: #ffffff;
    color: #16181d;
    font-size: 13px;
    border: 1px solid #dcdfe8;
    padding: 0 16px;
    height: 36px;
    min-height: 36px;
    max-height: 36px;
    border-radius: 18px;
}

QLineEdit:focus, QLineEdit#outputBoxMonospace:focus {
    border: 1px solid #aeb3c2;
    border-radius: 18px;
}

QPushButton#btnBrowseDest {
    background-color: #16181d;
    color: #ffffff;
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    padding: 0 16px;
    font-weight: 700;
    font-size: 13px;
    border: none;
}

QPushButton#btnBrowseDest:hover {
    background-color: #2b2e36;
    border-radius: 17px;
}

QPushButton#btnBrowseDest:pressed {
    background-color: #3f424c;
    border-radius: 17px;
}

QPushButton#btnCancel {
    background-color: #eceef4;
    color: #16181d;
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    padding: 0 16px;
    font-size: 13px;
    font-weight: 600;
    border: none;
}

QPushButton#btnCancel:hover {
    background-color: #e1e4ed;
    border-radius: 17px;
}

QPushButton#btnCancel:pressed {
    background-color: #dcdfe8;
    border-radius: 17px;
}

QPushButton#btnCancel:disabled {
    background-color: #eceef4;
    color: #9a9eac;
    border-radius: 17px;
    border: none;
}

QComboBox {
    background-color: #ffffff;
    color: #16181d;
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    padding: 0 14px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #dcdfe8;
}

QComboBox:hover {
    background-color: #eceef4;
    border-radius: 17px;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBoxPrivateContainer,
QFrame[class="QComboBoxPrivateContainer"] {
    background-color: transparent;
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #16181d;
    border: 1px solid #dcdfe8;
    border-radius: 16px;
    padding: 6px;
    selection-background-color: #eceef4;
    selection-color: #16181d;
    outline: none;
}

QComboBox QAbstractItemView::item {
    border-radius: 10px;
    padding: 6px 12px;
    min-height: 28px;
    color: #16181d;
}

QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected {
    background-color: #eceef4;
    color: #16181d;
    border-radius: 10px;
}

/* Progress Bar (.prog) */
QProgressBar {
    background-color: #e1e4ed;
    border-radius: 7px;
    height: 14px;
    min-height: 14px;
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

/* Stepper Granularity Control & Sensitivity Stepper Pill Group */
QFrame#sensitivitySelector, QFrame#stepperGroup {
    background-color: #eceef4;
    border-radius: 17px;
    border: 1px solid #dcdfe8;
    padding: 2px 4px;
    min-height: 28px;
    max-height: 34px;
}

QFrame#sensitivitySelector QPushButton,
QFrame#stepperGroup QPushButton,
QPushButton.pillSegmentBtn {
    border-radius: 13px;
    font-size: 12px;
    font-weight: 600;
    padding: 3px 12px;
    border: none;
    background-color: transparent;
    color: #6a7080;
    min-height: 24px;
    max-height: 26px;
}

QFrame#sensitivitySelector QPushButton:hover,
QFrame#stepperGroup QPushButton:hover,
QPushButton.pillSegmentBtn:hover {
    background-color: #e1e4ed;
    color: #16181d;
    border-radius: 13px;
}

QFrame#sensitivitySelector QPushButton:pressed,
QFrame#stepperGroup QPushButton:pressed,
QPushButton.pillSegmentBtn:pressed {
    background-color: #d2d6e3;
    color: #16181d;
    border-radius: 13px;
}

QFrame#sensitivitySelector QPushButton[active="true"],
QFrame#stepperGroup QPushButton[active="true"],
QPushButton.pillSegmentBtn[active="true"] {
    background-color: #16181d;
    color: #ffffff;
    font-weight: 700;
    border-radius: 13px;
}

/* Offset Display Box (.off) */
QFrame.offBox, QFrame.offsetCallout {
    background-color: #ebedf4;
    border-radius: 20px;
    border: none;
}

QLabel.largeOffsetDisplay {
    font-size: 38px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #16181d;
    background: transparent;
    border: none;
}

QPushButton#btnResetOffset, QPushButton#btn_reset {
    background-color: transparent;
    border: none;
    color: #16181d;
    font-size: 13px;
    font-weight: 600;
    padding: 4px 8px;
    border-radius: 10px;
}

QPushButton#btnResetOffset:hover, QPushButton#btn_reset:hover {
    color: #4081f7;
    background-color: rgba(64, 129, 247, 0.08);
}

QPushButton#btnResetOffset:pressed, QPushButton#btn_reset:pressed {
    color: #2563eb;
    background-color: rgba(64, 129, 247, 0.16);
}

QLabel#chipTrack, QLabel.chipTrack {
    background-color: #dbe7ff;
    color: #4081f7;
    border-radius: 14px;
    height: 28px;
    min-height: 28px;
    max-height: 28px;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 600;
    border: none;
    qproperty-alignment: AlignCenter;
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

QSlider {
    background: transparent;
    border: none;
    min-height: 28px;
    height: 28px;
}

QSlider:focus {
    border: none;
    outline: none;
}

QSlider::groove:horizontal {
    height: 8px;
    background: #e0e3ec;
    border-radius: 4px;
}

QSlider::sub-page:horizontal {
    height: 8px;
    background: #4081f7;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 3px solid #4081f7;
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 10px;
}

QSlider::handle:horizontal:hover {
    border-color: #2563eb;
}

/* Step Nudge Buttons (.steps) */
QPushButton.stepBtn, QPushButton.btnNudge {
    background-color: #ebedf4;
    border-radius: 18px;
    padding: 0;
    font-size: 12px;
    font-weight: 700;
    color: #16181d;
    border: none;
    min-height: 36px;
    height: 36px;
}

QPushButton.stepBtn:hover, QPushButton.btnNudge:hover {
    background-color: #e1e4ee;
    border-radius: 18px;
}

QPushButton.stepBtn:pressed, QPushButton.btnNudge:pressed {
    background-color: #d5d9e5;
    border-radius: 18px;
}

QPushButton.stepBtn:disabled, QPushButton.btnNudge:disabled {
    background-color: #f2f3f8;
    color: #9a9eac;
    border-radius: 18px;
}

/* Metrics Grid (.mets) */
QFrame.metBox, QFrame.metricCallout {
    background-color: #ebedf4;
    border-radius: 18px;
    border: none;
}

QLabel.metVal, QLabel.monoValue {
    font-size: 18px;
    font-weight: 700;
    color: #16181d;
}

QLabel.metVal[analyzed="false"] {
    color: #596579;
}

/* Note Pill (.note) */
QFrame.notePill, QFrame#frameNote {
    background-color: #ebedf4;
    border-radius: 18px;
    border: none;
    min-height: 36px;
    height: 36px;
}

QLabel.greenDot {
    background-color: #2fb16b;
    border-radius: 4px;
    width: 8px;
    height: 8px;
    min-width: 8px;
    max-width: 8px;
    min-height: 8px;
    max-height: 8px;
    border: none;
}

QLabel#lblDiagnosisNote {
    color: #596579;
    font-size: 12px;
    font-weight: 500;
    background: transparent;
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
    border-radius: 13px;
    height: 26px;
    min-height: 26px;
    max-height: 26px;
    padding: 0 14px;
    font-weight: 600;
    font-size: 13px;
    border: none;
    qproperty-alignment: AlignCenter;
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
    border-radius: 20px;
    height: 40px;
    min-height: 40px;
    max-height: 40px;
    padding: 0 16px;
    font-weight: 600;
    color: #6a7080;
    font-size: 13px;
    border: none;
}

QPushButton.markerBtn:hover {
    background-color: #e1e4ed;
    color: #16181d;
    border-radius: 20px;
}

QPushButton.markerBtn:checked, QPushButton.markerBtn.on, QPushButton.markerBtn[on="true"] {
    background-color: #16181d;
    color: #ffffff;
    border-radius: 20px;
}

QPushButton.markerBtn:pressed {
    background-color: #d3d6e0;
    border-radius: 20px;
}

QPushButton.markerBtn:disabled {
    background-color: #f1f2f6;
    color: #9a9eac;
    border-radius: 20px;
    border: none;
}

QPushButton#btnStopPreview:disabled {
    background-color: #f1f2f6;
    color: #a0a4b0;
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    padding: 0 14px;
    border: none;
}

/* Floating Dock (.dock) */
QFrame.floatingDock, QFrame#floatingDock, QFrame#eventLogDrawer {
    background-color: #ffffff;
    border-radius: 28px; /* border-radius: 34px; */
    border: none;
}

QLabel#badgeEventCount, QLabel.badgeEventCount {
    border-radius: 14px;
    height: 28px;
    min-height: 28px;
    max-height: 28px;
    background-color: #eceef4;
    color: #555864;
    padding: 0 12px;
    font-size: 12px;
    font-weight: 600;
    border: none;
    qproperty-alignment: AlignCenter;
}

QFrame.floatingDock QPushButton, QFrame#floatingDock QPushButton, QFrame#eventLogDrawer QPushButton,
QPushButton#btnDockClear, QPushButton#btnDockToggle {
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    background-color: #eceef4;
    color: #16181d;
    padding: 0 14px;
    font-size: 13px;
    font-weight: 600;
    border: none;
}

QFrame.floatingDock QPushButton:hover, QFrame#floatingDock QPushButton:hover,
QPushButton#btnDockClear:hover, QPushButton#btnDockToggle:hover {
    background-color: #e1e4ed;
    border-radius: 17px;
}

QFrame.floatingDock QPushButton:pressed, QFrame#floatingDock QPushButton:pressed,
QPushButton#btnDockClear:pressed, QPushButton#btnDockToggle:pressed {
    background-color: #d3d6e0;
    border-radius: 17px;
}

QFrame.floatingDock QPushButton:disabled, QFrame#floatingDock QPushButton:disabled,
QPushButton#btnDockClear:disabled, QPushButton#btnDockToggle:disabled {
    background-color: #f1f2f6;
    color: #9a9eac;
    border-radius: 17px;
}

QLabel.logTitle, QLabel#dockTitle {
    font-size: 14px;
    font-weight: 700;
    color: #16181d;
    background: transparent;
    border: none;
}

/* Floating Action Dock (Compact TiltedDock Nativo) */
QFrame#floatingActionDock, QFrame.floatingActionDock {
    background-color: rgba(255, 255, 255, 0.85);
    border-radius: 26px;
    border: 1px solid #e1e4ed;
}

QPushButton#dockItemBtn, QAbstractButton.dockItemBtn {
    border-radius: 20px;
    width: 40px;
    min-width: 40px;
    max-width: 40px;
    height: 40px;
    min-height: 40px;
    max-height: 40px;
    background-color: transparent;
    border: none;
    padding: 0px;
}

QPushButton#dockItemBtn:hover, QAbstractButton.dockItemBtn:hover {
    background-color: transparent;
    border: none;
}

QPushButton#dockItemBtn:pressed, QAbstractButton.dockItemBtn:pressed {
    background-color: transparent;
    border: none;
}

QLabel#dockBadge {
    background-color: #e1e4ed;
    color: #16181d;
    border: 1px solid #cbcfdc;
    border-radius: 8px;
    font-size: 10px;
    font-weight: 700;
    padding: 0 4px;
    min-height: 16px;
    max-height: 16px;
}

QLabel#dockTooltip {
    background-color: #ffffff;
    color: #16181d;
    border: 1px solid #d3d6e0;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
}

QLabel#floatingToast, QFrame#floatingToast {
    background-color: #ffffff;
    color: #16181d;
    border: 1px solid #d3d6e0;
    border-radius: 18px;
    font-size: 12px;
    font-weight: 600;
    padding: 8px 18px;
}

QFrame#eventLogPopoverContainer, QFrame#versionInfoPopoverContainer {
    background-color: #ffffff;
    border: 1px solid #e1e4ed;
    border-radius: 20px;
}


QPlainTextEdit {
    background-color: #ffffff;
    color: #6a7080;
    border: 1px solid #dcdfe8;
    border-radius: 20px;
    font-size: 13px;
    padding: 10px;
}

QPlainTextEdit#dockTextEdit {
    background-color: #ffffff;
    color: #6a7080;
    border: 1px solid #dcdfe8;
    border-radius: 18px;
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
    border-radius: 17px;
    height: 34px;
    min-height: 34px;
    max-height: 34px;
    padding: 0 12px;
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
    border-radius: 18px;
    height: 36px;
    min-height: 36px;
    max-height: 36px;
    background-color: #eceef4;
    color: #16181d;
    padding: 0 18px;
    font-weight: 600;
    border: none;
}

QPushButton#collapsibleHeaderBtn:hover, QPushButton.collapsibleBtn:hover {
    background-color: #e1e4ed;
    border-radius: 18px;
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
        return f"border-radius: 22px; height: 44px; min-height: 44px; max-height: 44px; /* border-radius: 999px; */ background-color: {bg}; color: {fg}; font-weight: 700; padding: 0 26px; border: none;"
    bg = "#26272d" if mode == "dark" else "#eceef4"
    fg = "#f2f3f7" if mode == "dark" else "#16181d"
    return f"border-radius: 17px; height: 34px; min-height: 34px; max-height: 34px; /* border-radius: 999px; */ background-color: {bg}; color: {fg}; font-weight: 600; padding: 0 14px; border: none;"


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


