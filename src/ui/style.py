"""Precision Bench / Media Alignment Workbench strictly monochrome design system for SyncFrame."""

from typing import Literal

# ==============================================================================
# Dark Theme QSS (Neutral Monochrome Dark: #0d0d0d base, #141414 cards, #ffffff accents)
# ==============================================================================
DARK_THEME_QSS = """
/* Global Window & Typography (Workbench Precision Dark) */
QWidget {
    background-color: #0d0d0d;
    color: #ffffff;
    font-family: 'Inter', 'Segoe UI', 'Liberation Sans', -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #383838;
    selection-color: #ffffff;
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
    background-color: #141414;
    border-bottom: 1px solid #383838;
}

QLabel#brandTitle {
    background-color: transparent;
    color: #ffffff;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: -0.4px;
    border: none;
}

QLabel#brandSubtitle {
    background-color: transparent;
    color: #a8a8a8;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.2px;
    border: none;
}

QLabel#topCrumb {
    background-color: transparent;
    color: #a8a8a8;
    font-size: 12px;
    border: none;
}

QLabel#topCrumb strong {
    color: #ffffff;
    font-weight: 600;
}

/* Surface Panels and Cards */
QFrame.panelCard {
    background-color: #141414;
    border: 1px solid #383838;
    border-radius: 12px;
}

QFrame.bentoCard {
    background-color: #141414;
    border: 1px solid #383838;
    border-radius: 10px;
}

/* Subcards / Inset Containers */
QFrame.subCard {
    background-color: #1c1c1c;
    border: 1px solid #383838;
    border-radius: 8px;
}

/* Panel Header and Headings */
QLabel.sectionIndex {
    background-color: transparent;
    color: #a8a8a8;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    border: none;
}

QLabel.cardTitle {
    background-color: transparent;
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: -0.2px;
    border: none;
}

QLabel.subText {
    background-color: transparent;
    color: #a8a8a8;
    font-size: 11px;
    border: none;
}

QLabel.dropTitle {
    background-color: transparent;
    color: #ffffff;
    font-size: 14px;
    font-weight: 700;
    border: none;
}

QLabel.eyebrowText {
    background-color: transparent;
    color: #a8a8a8;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.0px;
    border: none;
}

/* Monospace Numbers & Metrics */
QLabel.monoValue {
    background-color: transparent;
    color: #ffffff;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 13px;
    font-weight: 700;
    border: none;
}

QLabel.largeOffsetDisplay {
    background-color: #1c1c1c;
    color: #ffffff;
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 6px 12px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: -0.5px;
}

/* Discrete Precision Telemetry Chips & Banners */
QLabel.diagnosisBanner {
    background-color: #1c1c1c;
    color: #ffffff;
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#lblTimecodeChip {
    background-color: #1c1c1c;
    color: #ffffff;
    border: 1px solid #383838;
    border-radius: 5px;
    padding: 2px 8px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    font-weight: 700;
}

/* Micro-chips and Badges */
QLabel.systemChip {
    background-color: #1c1c1c;
    color: #ffffff;
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

QLabel.codecChip {
    background-color: #242424;
    color: #ffffff;
    border: 1px solid #383838;
    border-radius: 4px;
    padding: 2px 6px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeNeutral {
    background-color: #1c1c1c;
    color: #a8a8a8;
    border: 1px solid #383838;
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 600;
}

QLabel.badgeSignal {
    background-color: #242424;
    color: #ffffff;
    border: 1px solid #ffffff;
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeGreen {
    background-color: #242424;
    color: #ffffff;
    border: 1px solid #383838;
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeAmber {
    background-color: #242424;
    color: #ffffff;
    border: 1px solid #383838;
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
    background-color: #ffffff;
    color: #0d0d0d;
    border: 1px solid #ffffff;
    font-weight: 700;
}

QPushButton.btnPrimary:hover {
    background-color: #e5e5e5;
    border-color: #e5e5e5;
}

QPushButton.btnPrimary:pressed {
    background-color: #cccccc;
    border-color: #cccccc;
}

QPushButton.btnSuccess {
    background-color: #ffffff;
    color: #0d0d0d;
    border: 1px solid #ffffff;
    font-weight: 700;
    font-size: 13px;
    padding: 8px 18px;
}

QPushButton.btnSuccess:hover {
    background-color: #e5e5e5;
    border-color: #e5e5e5;
}

QPushButton.btnSuccess:pressed {
    background-color: #cccccc;
    border-color: #cccccc;
}

QPushButton.btnSecondary {
    background-color: #1c1c1c;
    color: #ffffff;
    border: 1px solid #383838;
}

QPushButton.btnSecondary:hover {
    background-color: #242424;
    border-color: #a8a8a8;
}

QPushButton.btnSecondary:pressed {
    background-color: #141414;
    border-color: #ffffff;
}

QPushButton.btnDanger {
    background-color: #1c1c1c;
    color: #a8a8a8;
    border: 1px solid #383838;
}

QPushButton.btnDanger:hover {
    background-color: #242424;
    color: #ffffff;
    border-color: #ffffff;
}

QPushButton:disabled {
    background-color: #141414;
    color: #555555;
    border: 1px solid #242424;
}

/* Refined Telemetry Callout Containers */
QFrame.offsetCallout {
    background-color: #1c1c1c;
    border: 1px solid #383838;
    border-radius: 8px;
    padding: 8px 12px;
}

QFrame.metricCallout {
    background-color: #1c1c1c;
    border: 1px solid #383838;
    border-radius: 8px;
    padding: 6px 10px;
}

/* Modernized Lip-Sync Viewport & Marker Buttons */
QFrame.viewportScreen {
    background-color: #141414;
    border: 1px solid #383838;
    border-radius: 8px;
}

QPushButton.markerBtn {
    background-color: #1c1c1c;
    color: #a8a8a8;
    border: 1px solid #383838;
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 700;
}

QPushButton.markerBtn:hover {
    background-color: #242424;
    color: #ffffff;
    border-color: #a8a8a8;
}

QPushButton.markerBtn:checked {
    background-color: #ffffff;
    color: #0d0d0d;
    border: 1px solid #ffffff;
}

/* Unified Drop Zone States */
QFrame#dropFrameEmpty {
    border: 1px dashed #383838;
    border-radius: 11px;
    background-color: #141414;
}

QFrame#dropFrameSingle {
    border: 1px solid #383838;
    border-radius: 11px;
    background-color: #141414;
}

/* File Card Workbench */
QFrame.fileCardWorkbench {
    background-color: #1c1c1c;
    border: 1px solid #383838;
    border-radius: 8px;
}

/* Inputs & Comboboxes */
QLineEdit, QComboBox {
    background-color: #1c1c1c;
    color: #ffffff;
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
}

QLineEdit:focus, QComboBox:focus {
    border-color: #ffffff;
}

QComboBox::drop-down {
    border: none;
    padding-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #141414;
    color: #ffffff;
    border: 1px solid #383838;
    selection-background-color: #242424;
    selection-color: #ffffff;
}

/* Linear Offset Slider */
QSlider::groove:horizontal {
    height: 4px;
    background: #1c1c1c;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #383838;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 1px solid #ffffff;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

/* Progress Bar */
QProgressBar {
    background-color: #1c1c1c;
    border: 1px solid #383838;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-size: 11px;
    font-weight: 700;
    max-height: 14px;
}

QProgressBar::chunk {
    background-color: #ffffff;
    border-radius: 5px;
}

/* Checkboxes */
QCheckBox {
    color: #a8a8a8;
    font-size: 11px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #383838;
    border-radius: 4px;
    background-color: #141414;
}

QCheckBox::indicator:hover {
    border-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #ffffff;
    border-color: #ffffff;
}

/* Retractable Collapsible Section Toggle */
QPushButton#collapsibleHeaderBtn {
    background-color: transparent;
    color: #ffffff;
    border: none;
    font-size: 12px;
    font-weight: 700;
    text-align: left;
    padding: 4px 0;
}

/* Terminal & Log Drawer */
QPlainTextEdit {
    background-color: #0d0d0d;
    color: #ffffff;
    border: 1px solid #383838;
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
    background: #242424;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #383838;
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
    background: #242424;
    min-width: 24px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #383838;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    height: 0;
}

/* Modals */
QDialog {
    background-color: #0d0d0d;
    border: 1px solid #383838;
}
"""

# ==============================================================================
# Light Theme QSS (Neutral Monochrome Light: #f4f4f4 base, #ffffff cards, #111111 accents)
# ==============================================================================
LIGHT_THEME_QSS = """
/* Global Window & Typography (Workbench Precision Light) */
QWidget {
    background-color: #f4f4f4;
    color: #111111;
    font-family: 'Inter', 'Segoe UI', 'Liberation Sans', -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #d1d1d1;
    selection-color: #111111;
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
    border-bottom: 1px solid #d1d1d1;
}

QLabel#brandTitle {
    background-color: transparent;
    color: #111111;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: -0.4px;
    border: none;
}

QLabel#brandSubtitle {
    background-color: transparent;
    color: #4a4a4a;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.2px;
    border: none;
}

QLabel#topCrumb {
    background-color: transparent;
    color: #4a4a4a;
    font-size: 12px;
    border: none;
}

QLabel#topCrumb strong {
    color: #111111;
    font-weight: 600;
}

/* Surface Panels and Cards */
QFrame.panelCard {
    background-color: #ffffff;
    border: 1px solid #d1d1d1;
    border-radius: 12px;
}

QFrame.bentoCard {
    background-color: #ffffff;
    border: 1px solid #d1d1d1;
    border-radius: 10px;
}

/* Subcards / Inset Containers */
QFrame.subCard {
    background-color: #ededed;
    border: 1px solid #d1d1d1;
    border-radius: 8px;
}

/* Panel Header and Headings */
QLabel.sectionIndex {
    background-color: transparent;
    color: #4a4a4a;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    border: none;
}

QLabel.cardTitle {
    background-color: transparent;
    color: #111111;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: -0.2px;
    border: none;
}

QLabel.subText {
    background-color: transparent;
    color: #4a4a4a;
    font-size: 11px;
    border: none;
}

QLabel.dropTitle {
    background-color: transparent;
    color: #111111;
    font-size: 14px;
    font-weight: 700;
    border: none;
}

QLabel.eyebrowText {
    background-color: transparent;
    color: #4a4a4a;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.0px;
    border: none;
}

/* Monospace Numbers & Metrics */
QLabel.monoValue {
    background-color: transparent;
    color: #111111;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 13px;
    font-weight: 700;
    border: none;
}

QLabel.largeOffsetDisplay {
    background-color: #ededed;
    color: #111111;
    border: 1px solid #d1d1d1;
    border-radius: 6px;
    padding: 6px 12px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: -0.5px;
}

/* Discrete Precision Telemetry Chips & Banners */
QLabel.diagnosisBanner {
    background-color: #ededed;
    color: #111111;
    border: 1px solid #d1d1d1;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#lblTimecodeChip {
    background-color: #ededed;
    color: #111111;
    border: 1px solid #d1d1d1;
    border-radius: 5px;
    padding: 2px 8px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    font-weight: 700;
}

/* Micro-chips and Badges */
QLabel.systemChip {
    background-color: #ededed;
    color: #111111;
    border: 1px solid #d1d1d1;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

QLabel.codecChip {
    background-color: #ededed;
    color: #111111;
    border: 1px solid #d1d1d1;
    border-radius: 4px;
    padding: 2px 6px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeNeutral {
    background-color: #f4f4f4;
    color: #4a4a4a;
    border: 1px solid #d1d1d1;
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 600;
}

QLabel.badgeSignal {
    background-color: #ededed;
    color: #111111;
    border: 1px solid #111111;
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeGreen {
    background-color: #ededed;
    color: #111111;
    border: 1px solid #d1d1d1;
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeAmber {
    background-color: #ededed;
    color: #111111;
    border: 1px solid #d1d1d1;
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
    background-color: #111111;
    color: #ffffff;
    border: 1px solid #111111;
    font-weight: 700;
}

QPushButton.btnPrimary:hover {
    background-color: #242424;
    border-color: #242424;
}

QPushButton.btnPrimary:pressed {
    background-color: #383838;
    border-color: #383838;
}

QPushButton.btnSuccess {
    background-color: #111111;
    color: #ffffff;
    border: 1px solid #111111;
    font-weight: 700;
    font-size: 13px;
    padding: 8px 18px;
}

QPushButton.btnSuccess:hover {
    background-color: #242424;
    border-color: #242424;
}

QPushButton.btnSuccess:pressed {
    background-color: #383838;
    border-color: #383838;
}

QPushButton.btnSecondary {
    background-color: #ededed;
    color: #111111;
    border: 1px solid #d1d1d1;
}

QPushButton.btnSecondary:hover {
    background-color: #ffffff;
    border-color: #111111;
}

QPushButton.btnSecondary:pressed {
    background-color: #d1d1d1;
    border-color: #111111;
}

QPushButton.btnDanger {
    background-color: #ededed;
    color: #4a4a4a;
    border: 1px solid #d1d1d1;
}

QPushButton.btnDanger:hover {
    background-color: #ffffff;
    color: #111111;
    border-color: #111111;
}

QPushButton:disabled {
    background-color: #ededed;
    color: #a8a8a8;
    border: 1px solid #d1d1d1;
}

/* Refined Telemetry Callout Containers */
QFrame.offsetCallout {
    background-color: #ededed;
    border: 1px solid #d1d1d1;
    border-radius: 8px;
    padding: 8px 12px;
}

QFrame.metricCallout {
    background-color: #ededed;
    border: 1px solid #d1d1d1;
    border-radius: 8px;
    padding: 6px 10px;
}

/* Modernized Lip-Sync Viewport & Marker Buttons */
QFrame.viewportScreen {
    background-color: #ffffff;
    border: 1px solid #d1d1d1;
    border-radius: 8px;
}

QPushButton.markerBtn {
    background-color: #ededed;
    color: #4a4a4a;
    border: 1px solid #d1d1d1;
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 700;
}

QPushButton.markerBtn:hover {
    background-color: #ffffff;
    color: #111111;
    border-color: #111111;
}

QPushButton.markerBtn:checked {
    background-color: #111111;
    color: #ffffff;
    border: 1px solid #111111;
}

/* Unified Drop Zone States */
QFrame#dropFrameEmpty {
    border: 1px dashed #d1d1d1;
    border-radius: 11px;
    background-color: #ffffff;
}

QFrame#dropFrameSingle {
    border: 1px solid #d1d1d1;
    border-radius: 11px;
    background-color: #ffffff;
}

/* File Card Workbench */
QFrame.fileCardWorkbench {
    background-color: #ededed;
    border: 1px solid #d1d1d1;
    border-radius: 8px;
}

/* Inputs & Comboboxes */
QLineEdit, QComboBox {
    background-color: #ffffff;
    color: #111111;
    border: 1px solid #d1d1d1;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
}

QLineEdit:focus, QComboBox:focus {
    border-color: #111111;
}

QComboBox::drop-down {
    border: none;
    padding-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #111111;
    border: 1px solid #d1d1d1;
    selection-background-color: #ededed;
    selection-color: #111111;
}

/* Linear Offset Slider */
QSlider::groove:horizontal {
    height: 4px;
    background: #ededed;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #d1d1d1;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #111111;
    border: 1px solid #111111;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

/* Progress Bar */
QProgressBar {
    background-color: #ededed;
    border: 1px solid #d1d1d1;
    border-radius: 6px;
    text-align: center;
    color: #111111;
    font-size: 11px;
    font-weight: 700;
    max-height: 14px;
}

QProgressBar::chunk {
    background-color: #111111;
    border-radius: 5px;
}

/* Checkboxes */
QCheckBox {
    color: #4a4a4a;
    font-size: 11px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #d1d1d1;
    border-radius: 4px;
    background-color: #ffffff;
}

QCheckBox::indicator:hover {
    border-color: #111111;
}

QCheckBox::indicator:checked {
    background-color: #111111;
    border-color: #111111;
}

/* Retractable Collapsible Section Toggle */
QPushButton#collapsibleHeaderBtn {
    background-color: transparent;
    color: #111111;
    border: none;
    font-size: 12px;
    font-weight: 700;
    text-align: left;
    padding: 4px 0;
}

/* Terminal & Log Drawer */
QPlainTextEdit {
    background-color: #ffffff;
    color: #111111;
    border: 1px solid #d1d1d1;
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
    background: #d1d1d1;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #a8a8a8;
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
    background: #d1d1d1;
    min-width: 24px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #a8a8a8;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    height: 0;
}

/* Modals */
QDialog {
    background-color: #ffffff;
    border: 1px solid #d1d1d1;
}
"""


def get_theme_stylesheet(mode: Literal["dark", "light"] = "dark") -> str:
    """Returns the QSS stylesheet for the requested precision bench theme."""
    return DARK_THEME_QSS if mode == "dark" else LIGHT_THEME_QSS


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
            background-color: #1c1c1c;
            border: 1px solid #383838;
            border-radius: 8px;
            padding: 8px 12px;
        }
        QFrame.metricCallout {
            background-color: #1c1c1c;
            border: 1px solid #383838;
            border-radius: 8px;
            padding: 6px 10px;
        }
        """
    return """
    QFrame.offsetCallout {
        background-color: #ededed;
        border: 1px solid #d1d1d1;
        border-radius: 8px;
        padding: 8px 12px;
    }
    QFrame.metricCallout {
        background-color: #ededed;
        border: 1px solid #d1d1d1;
        border-radius: 8px;
        padding: 6px 10px;
    }
    """


def get_player_viewport_style(mode: Literal["dark", "light"] = "dark") -> str:
    """Returns CSS styles for the preview monitor and lip-sync player controls."""
    if mode == "dark":
        return """
        QFrame.viewportScreen {
            background-color: #141414;
            border: 1px solid #383838;
            border-radius: 8px;
        }
        QPushButton.markerBtn {
            background-color: #1c1c1c;
            color: #a8a8a8;
            border: 1px solid #383838;
            border-radius: 5px;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: 700;
        }
        QPushButton.markerBtn:hover {
            background-color: #242424;
            color: #ffffff;
            border-color: #a8a8a8;
        }
        QPushButton.markerBtn:checked {
            background-color: #ffffff;
            color: #0d0d0d;
            border: 1px solid #ffffff;
        }
        """
    return """
    QFrame.viewportScreen {
        background-color: #ffffff;
        border: 1px solid #d1d1d1;
        border-radius: 8px;
    }
    QPushButton.markerBtn {
        background-color: #ededed;
        color: #4a4a4a;
        border: 1px solid #d1d1d1;
        border-radius: 5px;
        padding: 4px 8px;
        font-size: 11px;
        font-weight: 700;
    }
    QPushButton.markerBtn:hover {
        background-color: #ffffff;
        color: #111111;
        border-color: #111111;
    }
    QPushButton.markerBtn:checked {
        background-color: #111111;
        color: #ffffff;
        border: 1px solid #111111;
    }
    """


def get_clean_badge_style(radius: int = 6, bg: str = "#1c1c1c", border: str = "#383838") -> str:
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
            background-color: #242424;
            color: #ffffff;
            border: 1px solid #ffffff;
            border-radius: 6px;
            padding: 4px 8px;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
            font-weight: 700;
        """
    return """
        background-color: #1c1c1c;
        color: #ffffff;
        border: 1px solid #383838;
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
            color: #ffffff;
            font-size: 15px;
            font-weight: 800;
            letter-spacing: -0.4px;
            border: none;
        }
        QLabel#brandSubtitle {
            background-color: transparent;
            color: #a8a8a8;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
            font-size: 9px;
            font-weight: 600;
            letter-spacing: 1.2px;
            border: none;
        }
        QLabel#topCrumb {
            background-color: transparent;
            color: #a8a8a8;
            font-size: 12px;
            border: none;
            padding-left: 2px;
        }
        QLabel#topCrumb strong {
            color: #ffffff;
            font-weight: 600;
        }
    """
