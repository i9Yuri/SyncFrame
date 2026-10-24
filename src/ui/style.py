"""Precision Bench / Media Alignment Workbench strictly monochrome design system for SyncFrame."""

from typing import Literal

# ==============================================================================
# Dark Theme QSS (Neutral Monochrome Dark: #0a0b0d base, #111317 panels, #eef0f2 text, #282d34 borders)
# ==============================================================================
DARK_THEME_QSS = """
/* Global Window & Typography (Workbench Precision Dark) */
QWidget {
    background-color: #0a0b0d;
    color: #eef0f2;
    font-family: 'Inter', 'Segoe UI', 'Liberation Sans', -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #282d34;
    selection-color: #eef0f2;
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

/* Workbench Topbar */
QWidget#workbenchTopbar {
    background-color: #111317;
    border-bottom: 1px solid #282d34;
}

QLabel#brandTitle {
    background-color: transparent;
    color: #eef0f2;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: -0.4px;
    border: none;
}

QLabel#brandSubtitle {
    background-color: transparent;
    color: #7e8792;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.2px;
    border: none;
}

QLabel#topCrumb {
    background-color: transparent;
    color: #7e8792;
    font-size: 12px;
    border: none;
}

QLabel#topCrumb strong {
    color: #eef0f2;
    font-weight: 600;
}

/* Surface Panels and Cards */
QFrame.panelCard, QFrame.bentoCard {
    background-color: #111317;
    border: 1px solid #282d34;
    border-radius: 10px;
}

QFrame#eventLogDrawer {
    background-color: #111317;
    border: 1px solid #282d34;
    border-radius: 10px;
}

/* Subcards / Inset Containers */
QFrame.subCard {
    background-color: #181b20;
    border: 1px solid #282d34;
    border-radius: 8px;
}

/* Panel Header and Headings */
QLabel.sectionIndex {
    background-color: transparent;
    color: #7e8792;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    border: none;
}

QLabel.cardTitle {
    background-color: transparent;
    color: #eef0f2;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: -0.2px;
    border: none;
}

QLabel.subText {
    background-color: transparent;
    color: #7e8792;
    font-size: 11px;
    border: none;
}

QLabel.dropTitle {
    background-color: transparent;
    color: #eef0f2;
    font-size: 14px;
    font-weight: 700;
    border: none;
}

QLabel.logTitle {
    background-color: transparent;
    color: #eef0f2;
    font-size: 12px;
    font-weight: 700;
    border: none;
}

QLabel.eyebrowText {
    background-color: transparent;
    color: #7e8792;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.0px;
    border: none;
}

/* Monospace Numbers & Metrics */
QLabel.monoValue {
    background-color: transparent;
    color: #eef0f2;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 13px;
    font-weight: 700;
    border: none;
}

QLabel.largeOffsetDisplay {
    background-color: #181b20;
    color: #eef0f2;
    border: 1px solid #282d34;
    border-radius: 6px;
    padding: 6px 12px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: -0.5px;
}

/* Discrete Precision Telemetry Chips & Banners */
QLabel.diagnosisBanner {
    background-color: #181b20;
    color: #eef0f2;
    border: 1px solid #282d34;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#lblTimecodeChip {
    background-color: #181b20;
    color: #eef0f2;
    border: 1px solid #282d34;
    border-radius: 5px;
    padding: 2px 8px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    font-weight: 700;
}

/* Micro-chips and Badges */
QLabel.systemChip {
    background-color: #181b20;
    color: #eef0f2;
    border: 1px solid #282d34;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

QLabel.codecChip {
    background-color: #181b20;
    color: #eef0f2;
    border: 1px solid #282d34;
    border-radius: 4px;
    padding: 2px 6px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeNeutral {
    background-color: #181b20;
    color: #7e8792;
    border: 1px solid #282d34;
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 600;
}

QLabel.badgeSignal {
    background-color: #181b20;
    color: #eef0f2;
    border: 1px solid #eef0f2;
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeGreen {
    background-color: #181b20;
    color: #eef0f2;
    border: 1px solid #282d34;
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeAmber {
    background-color: #181b20;
    color: #eef0f2;
    border: 1px solid #282d34;
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 700;
}

/* Buttons */
QPushButton {
    border-radius: 6px;
    font-weight: 600;
    font-size: 12px;
    padding: 6px 14px;
}

QPushButton.btnPrimary {
    background-color: #eef0f2;
    color: #0a0b0d;
    border: 1px solid #eef0f2;
    font-weight: 700;
}

QPushButton.btnPrimary:hover {
    background-color: #ffffff;
    border-color: #ffffff;
}

QPushButton.btnPrimary:pressed {
    background-color: #d1d1d1;
    border-color: #d1d1d1;
}

QPushButton.btnSuccess {
    background-color: #eef0f2;
    color: #0a0b0d;
    border: 1px solid #eef0f2;
    font-weight: 700;
    font-size: 13px;
    padding: 8px 18px;
}

QPushButton.btnSuccess:hover {
    background-color: #ffffff;
    border-color: #ffffff;
}

QPushButton.btnSuccess:pressed {
    background-color: #d1d1d1;
    border-color: #d1d1d1;
}

QPushButton.btnSecondary {
    background-color: #181b20;
    color: #eef0f2;
    border: 1px solid #282d34;
}

QPushButton.btnSecondary:hover {
    background-color: #242830;
    border-color: #eef0f2;
}

QPushButton.btnSecondary:pressed {
    background-color: #282d34;
    border-color: #eef0f2;
}

QPushButton.btnDanger {
    background-color: #181b20;
    color: #7e8792;
    border: 1px solid #282d34;
}

QPushButton.btnDanger:hover {
    background-color: #242830;
    color: #eef0f2;
    border-color: #eef0f2;
}

/* Precision Bench Markers */
QPushButton.markerBtn {
    background-color: #181b20;
    color: #7e8792;
    border: 1px solid #282d34;
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 700;
}

QPushButton.markerBtn:hover {
    background-color: #242830;
    color: #eef0f2;
    border-color: #7e8792;
}

QPushButton.markerBtn:checked {
    background-color: #eef0f2;
    color: #0a0b0d;
    border: 1px solid #eef0f2;
}

/* Unified Drop Zone States */
QFrame#dropFrameEmpty {
    border: 1px dashed #282d34;
    border-radius: 11px;
    background-color: #111317;
}

QFrame#dropFrameEmpty[dragOver="true"] {
    border: 1px dashed #eef0f2;
    background-color: #181b20;
}

QFrame#dropFrameSingle {
    border: 1px solid #282d34;
    border-radius: 11px;
    background-color: #111317;
}

/* File Card Workbench */
QFrame.fileCardWorkbench {
    background-color: #181b20;
    border: 1px solid #282d34;
    border-radius: 8px;
}

/* Dividers */
QFrame.dividerLine, QFrame#crumbSep {
    background-color: #282d34;
    border: none;
}

/* Inputs & Comboboxes */
QLineEdit, QComboBox {
    background-color: #181b20;
    color: #eef0f2;
    border: 1px solid #282d34;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
}

QLineEdit:focus, QComboBox:focus {
    border-color: #eef0f2;
}

QComboBox::drop-down {
    border: none;
    padding-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #111317;
    color: #eef0f2;
    border: 1px solid #282d34;
    selection-background-color: #242830;
    selection-color: #eef0f2;
}

/* Linear Offset Slider */
QSlider::groove:horizontal {
    height: 4px;
    background: #181b20;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #282d34;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #eef0f2;
    border: 1px solid #eef0f2;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

/* Progress Bar */
QProgressBar {
    background-color: #181b20;
    border: 1px solid #282d34;
    border-radius: 6px;
    text-align: center;
    color: #eef0f2;
    font-size: 11px;
    font-weight: 700;
    max-height: 14px;
}

QProgressBar::chunk {
    background-color: #eef0f2;
    border-radius: 5px;
}

/* Checkboxes */
QCheckBox {
    color: #7e8792;
    font-size: 11px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #282d34;
    border-radius: 4px;
    background-color: #111317;
}

QCheckBox::indicator:hover {
    border-color: #eef0f2;
}

QCheckBox::indicator:checked {
    background-color: #eef0f2;
    border-color: #eef0f2;
}

/* Retractable Collapsible Section Toggle */
QPushButton#collapsibleHeaderBtn {
    background-color: transparent;
    color: #eef0f2;
    border: none;
    font-size: 12px;
    font-weight: 700;
    text-align: left;
    padding: 4px 0;
}

/* Terminal & Log Drawer */
QPlainTextEdit {
    background-color: #0a0b0d;
    color: #eef0f2;
    border: 1px solid #282d34;
    border-radius: 6px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #242830;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #282d34;
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
    background: #242830;
    min-width: 24px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #282d34;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    height: 0;
}

/* Modals */
QDialog {
    background-color: #0a0b0d;
    border: 1px solid #282d34;
}
"""

# ==============================================================================
# Light Theme QSS (Neutral Monochrome Light: #f2f3f1 base, #ffffff cards, #191c1a text, #d9ddd7 borders)
# ==============================================================================
LIGHT_THEME_QSS = """
/* Global Window & Typography (Workbench Precision Light) */
QWidget {
    background-color: #f2f3f1;
    color: #191c1a;
    font-family: 'Inter', 'Segoe UI', 'Liberation Sans', -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #d9ddd7;
    selection-color: #191c1a;
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

/* Workbench Topbar */
QWidget#workbenchTopbar {
    background-color: #ffffff;
    border-bottom: 1px solid #d9ddd7;
}

QLabel#brandTitle {
    background-color: transparent;
    color: #191c1a;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: -0.4px;
    border: none;
}

QLabel#brandSubtitle {
    background-color: transparent;
    color: #424943;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.2px;
    border: none;
}

QLabel#topCrumb {
    background-color: transparent;
    color: #424943;
    font-size: 12px;
    border: none;
}

QLabel#topCrumb strong {
    color: #191c1a;
    font-weight: 600;
}

/* Surface Panels and Cards */
QFrame.panelCard, QFrame.bentoCard {
    background-color: #ffffff;
    border: 1px solid #d9ddd7;
    border-radius: 10px;
}

QFrame#eventLogDrawer {
    background-color: #f1f3ef;
    border: 1px solid #d9ddd7;
    border-radius: 10px;
}

/* Subcards / Inset Containers */
QFrame.subCard {
    background-color: #f1f3ef;
    border: 1px solid #d9ddd7;
    border-radius: 8px;
}

/* Panel Header and Headings */
QLabel.sectionIndex {
    background-color: transparent;
    color: #424943;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    border: none;
}

QLabel.cardTitle {
    background-color: transparent;
    color: #191c1a;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: -0.2px;
    border: none;
}

QLabel.subText {
    background-color: transparent;
    color: #424943;
    font-size: 11px;
    border: none;
}

QLabel.dropTitle {
    background-color: transparent;
    color: #191c1a;
    font-size: 14px;
    font-weight: 700;
    border: none;
}

QLabel.logTitle {
    background-color: transparent;
    color: #191c1a;
    font-size: 12px;
    font-weight: 700;
    border: none;
}

QLabel.eyebrowText {
    background-color: transparent;
    color: #424943;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.0px;
    border: none;
}

/* Monospace Numbers & Metrics */
QLabel.monoValue {
    background-color: transparent;
    color: #191c1a;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 13px;
    font-weight: 700;
    border: none;
}

QLabel.largeOffsetDisplay {
    background-color: #f1f3ef;
    color: #191c1a;
    border: 1px solid #d9ddd7;
    border-radius: 6px;
    padding: 6px 12px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: -0.5px;
}

/* Discrete Precision Telemetry Chips & Banners */
QLabel.diagnosisBanner {
    background-color: #f1f3ef;
    color: #191c1a;
    border: 1px solid #d9ddd7;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#lblTimecodeChip {
    background-color: #f1f3ef;
    color: #191c1a;
    border: 1px solid #d9ddd7;
    border-radius: 5px;
    padding: 2px 8px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    font-weight: 700;
}

/* Micro-chips and Badges */
QLabel.systemChip {
    background-color: #f1f3ef;
    color: #191c1a;
    border: 1px solid #d9ddd7;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

QLabel.codecChip {
    background-color: #f1f3ef;
    color: #191c1a;
    border: 1px solid #d9ddd7;
    border-radius: 4px;
    padding: 2px 6px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeNeutral {
    background-color: #e8ebe6;
    color: #424943;
    border: 1px solid #d9ddd7;
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 600;
}

QLabel.badgeSignal {
    background-color: #e8ebe6;
    color: #191c1a;
    border: 1px solid #191c1a;
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeGreen {
    background-color: #e8ebe6;
    color: #191c1a;
    border: 1px solid #191c1a;
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeAmber {
    background-color: #e8ebe6;
    color: #191c1a;
    border: 1px solid #d9ddd7;
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 700;
}

/* Buttons */
QPushButton {
    border-radius: 6px;
    font-weight: 600;
    font-size: 12px;
    padding: 6px 14px;
}

QPushButton.btnPrimary {
    background-color: #191c1a;
    color: #ffffff;
    border: 1px solid #191c1a;
    font-weight: 700;
}

QPushButton.btnPrimary:hover {
    background-color: #383d39;
    border-color: #383d39;
}

QPushButton.btnPrimary:pressed {
    background-color: #555c56;
    border-color: #555c56;
}

QPushButton.btnSuccess {
    background-color: #191c1a;
    color: #ffffff;
    border: 1px solid #191c1a;
    font-weight: 700;
    font-size: 13px;
    padding: 8px 18px;
}

QPushButton.btnSuccess:hover {
    background-color: #383d39;
    border-color: #383d39;
}

QPushButton.btnSuccess:pressed {
    background-color: #555c56;
    border-color: #555c56;
}

QPushButton.btnSecondary {
    background-color: #ffffff;
    color: #191c1a;
    border: 1px solid #d9ddd7;
}

QPushButton.btnSecondary:hover {
    background-color: #e8ebe6;
    color: #191c1a;
    border-color: #191c1a;
}

QPushButton.btnSecondary:pressed {
    background-color: #d9ddd7;
    color: #191c1a;
    border-color: #191c1a;
}

QPushButton.btnDanger {
    background-color: #ffffff;
    color: #424943;
    border: 1px solid #d9ddd7;
}

QPushButton.btnDanger:hover {
    background-color: #e8ebe6;
    color: #191c1a;
    border-color: #191c1a;
}

/* Precision Bench Markers */
QPushButton.markerBtn {
    background-color: #ededed;
    color: #424943;
    border: 1px solid #d9ddd7;
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 700;
}

QPushButton.markerBtn:hover {
    background-color: #ffffff;
    color: #191c1a;
    border-color: #191c1a;
}

QPushButton.markerBtn:checked {
    background-color: #191c1a;
    color: #ffffff;
    border: 1px solid #191c1a;
}

/* Unified Drop Zone States */
QFrame#dropFrameEmpty {
    border: 1px dashed #b9c0b7;
    border-radius: 11px;
    background-color: #ffffff;
}

QFrame#dropFrameEmpty[dragOver="true"] {
    border: 1px dashed #191c1a;
    background-color: #f1f3ef;
}

QFrame#dropFrameSingle {
    border: 1px solid #d9ddd7;
    border-radius: 11px;
    background-color: #ffffff;
}

/* File Card Workbench */
QFrame.fileCardWorkbench {
    background-color: #f1f3ef;
    border: 1px solid #d9ddd7;
    border-radius: 8px;
}

/* Dividers */
QFrame.dividerLine, QFrame#crumbSep {
    background-color: #d9ddd7;
    border: none;
}

/* Inputs & Comboboxes */
QLineEdit, QComboBox {
    background-color: #ffffff;
    color: #191c1a;
    border: 1px solid #d9ddd7;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
}

QLineEdit:focus, QComboBox:focus {
    border-color: #191c1a;
}

QComboBox::drop-down {
    border: none;
    padding-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #191c1a;
    border: 1px solid #d9ddd7;
    selection-background-color: #e8ebe6;
    selection-color: #191c1a;
}

/* Linear Offset Slider */
QSlider::groove:horizontal {
    height: 4px;
    background: #e8ebe6;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #d9ddd7;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #191c1a;
    border: 1px solid #191c1a;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

/* Progress Bar */
QProgressBar {
    background-color: #f1f3ef;
    border: 1px solid #d9ddd7;
    border-radius: 6px;
    text-align: center;
    color: #191c1a;
    font-size: 11px;
    font-weight: 700;
    max-height: 14px;
}

QProgressBar::chunk {
    background-color: #191c1a;
    border-radius: 5px;
}

/* Checkboxes */
QCheckBox {
    color: #424943;
    font-size: 11px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #d9ddd7;
    border-radius: 4px;
    background-color: #ffffff;
}

QCheckBox::indicator:hover {
    border-color: #191c1a;
}

QCheckBox::indicator:checked {
    background-color: #191c1a;
    border-color: #191c1a;
}

/* Retractable Collapsible Section Toggle */
QPushButton#collapsibleHeaderBtn {
    background-color: transparent;
    color: #191c1a;
    border: none;
    font-size: 12px;
    font-weight: 700;
    text-align: left;
    padding: 4px 0;
}

/* Terminal & Log Drawer */
QPlainTextEdit {
    background-color: #ffffff;
    color: #191c1a;
    border: 1px solid #d9ddd7;
    border-radius: 6px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #d9ddd7;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #b9c0b7;
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
    background: #d9ddd7;
    min-width: 24px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #b9c0b7;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    height: 0;
}

/* Modals */
QDialog {
    background-color: #ffffff;
    border: 1px solid #d9ddd7;
}
"""


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


def get_telemetry_badge_style(mode: Literal["dark", "light"] = "dark") -> str:
    """Returns CSS styles for telemetry callouts and contrast badges."""
    if mode == "dark":
        return """
        QFrame.offsetCallout {
            background-color: #181b20;
            border: 1px solid #282d34;
            border-radius: 8px;
            padding: 8px 12px;
        }
        QFrame.metricCallout {
            background-color: #181b20;
            border: 1px solid #282d34;
            border-radius: 8px;
            padding: 6px 10px;
        }
        """
    return """
    QFrame.offsetCallout {
        background-color: #f1f3ef;
        border: 1px solid #d9ddd7;
        border-radius: 8px;
        padding: 8px 12px;
    }
    QFrame.metricCallout {
        background-color: #f1f3ef;
        border: 1px solid #d9ddd7;
        border-radius: 8px;
        padding: 6px 10px;
    }
    """


def get_player_viewport_style(mode: Literal["dark", "light"] = "dark") -> str:
    """Returns CSS styles for the preview monitor and lip-sync player controls."""
    if mode == "dark":
        return """
        QFrame.viewportScreen {
            background-color: #111317;
            border: 1px solid #282d34;
            border-radius: 8px;
        }
        QPushButton.markerBtn {
            background-color: #181b20;
            color: #7e8792;
            border: 1px solid #282d34;
            border-radius: 5px;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: 700;
        }
        QPushButton.markerBtn:hover {
            background-color: #242830;
            color: #eef0f2;
            border-color: #7e8792;
        }
        QPushButton.markerBtn:checked {
            background-color: #eef0f2;
            color: #0a0b0d;
            border: 1px solid #eef0f2;
        }
        """
    return """
    QFrame.viewportScreen {
        background-color: #ffffff;
        border: 1px solid #d9ddd7;
        border-radius: 8px;
    }
    QPushButton.markerBtn {
        background-color: #ededed;
        color: #424943;
        border: 1px solid #d9ddd7;
        border-radius: 5px;
        padding: 4px 8px;
        font-size: 11px;
        font-weight: 700;
    }
    QPushButton.markerBtn:hover {
        background-color: #ffffff;
        color: #191c1a;
        border-color: #191c1a;
    }
    QPushButton.markerBtn:checked {
        background-color: #191c1a;
        color: #ffffff;
        border: 1px solid #191c1a;
    }
    """


def get_clean_badge_style(radius: int = 6, bg: str = "#181b20", border: str = "#282d34") -> str:
    """Returns CSS properties for clean, high-density micro-badges with smooth border-radius."""
    return f"""
        background-color: {bg};
        border: 1px solid {border};
        border-radius: {radius}px;
        padding: 3px 8px;
    """


def get_telemetry_display_style(is_accent: bool = False) -> str:
    """Returns CSS properties for precision telemetry boxes with rounded corners and no hard black backgrounds."""
    if is_accent:
        return """
            background-color: #242830;
            color: #eef0f2;
            border: 1px solid #eef0f2;
            border-radius: 6px;
            padding: 4px 8px;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
            font-weight: 700;
        """
    return """
        background-color: #181b20;
        color: #eef0f2;
        border: 1px solid #282d34;
        border-radius: 6px;
        padding: 4px 10px;
        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
        font-weight: 700;
    """


def get_topbar_brand_style() -> str:
    """Returns CSS styling for the topbar branding block with zero hard backgrounds and clean vector alignment."""
    return """
        QLabel#brandTitle {
            background-color: transparent;
            color: #eef0f2;
            font-size: 15px;
            font-weight: 800;
            letter-spacing: -0.4px;
            border: none;
        }
        QLabel#brandSubtitle {
            background-color: transparent;
            color: #7e8792;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
            font-size: 9px;
            font-weight: 600;
            letter-spacing: 1.2px;
            border: none;
        }
        QLabel#topCrumb {
            background-color: transparent;
            color: #7e8792;
            font-size: 12px;
            border: none;
            padding-left: 2px;
        }
        QLabel#topCrumb strong {
            color: #eef0f2;
            font-weight: 600;
        }
    """
