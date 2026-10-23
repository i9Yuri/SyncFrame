"""Precision Bench / Media Alignment Workbench design system and stylesheet generator for SyncFrame."""

from typing import Literal

# ==============================================================================
# Dark Theme QSS (Primary: #0a0b0d base, #111317 panels, #d9f56b signal accent)
# ==============================================================================
DARK_THEME_QSS = """
/* Global Window & Typography (Workbench Precision Dark) */
QWidget {
    background-color: #0a0b0d;
    color: #eef0f2;
    font-family: 'Inter', 'Segoe UI', 'Liberation Sans', -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #d9f56b;
    selection-color: #15190b;
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
    background-color: #0e1013;
    border-bottom: 1px solid #282d34;
}

QLabel#brandTitle {
    color: #eef0f2;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: -0.4px;
}

QLabel#brandSubtitle {
    color: #7e8792;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.2px;
}

QLabel#topCrumb {
    color: #7e8792;
    font-size: 12px;
    border-left: 1px solid #282d34;
    padding-left: 14px;
}

QLabel#topCrumb strong {
    color: #c1c6cd;
    font-weight: 600;
}

/* Pipeline Stepper Bar */
QFrame#pipelineStepperFrame {
    background-color: #111317;
    border: 1px solid #282d34;
    border-radius: 9px;
    padding: 3px;
}

QPushButton.pipeStepBtn {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 7px;
    color: #7e8792;
    padding: 7px 12px;
    text-align: left;
    font-weight: 600;
    font-size: 11px;
}

QPushButton.pipeStepBtn:hover {
    background-color: #15181d;
    color: #eef0f2;
}

QPushButton.pipeStepBtn[active="true"] {
    background-color: #191d22;
    border-color: #3b424c;
    color: #eef0f2;
}

QPushButton.pipeStepBtn[done="true"] {
    background-color: transparent;
    color: #bce7a0;
}

/* Surface Panels and Cards */
QFrame.panelCard, QFrame.bentoCard {
    background-color: #111317;
    border: 1px solid #282d34;
    border-radius: 12px;
}

QFrame.panelCard:hover, QFrame.bentoCard:hover {
    border-color: #3b424c;
}

/* Subcards / Inset Containers */
QFrame.subCard, QFrame.auditCard {
    background-color: #0e1013;
    border: 1px solid #282d34;
    border-radius: 8px;
    padding: 10px;
}

/* Panel Header and Headings */
QWidget.panelHead {
    border-bottom: 1px solid #282d34;
}

QLabel.sectionIndex {
    background-color: #15181d;
    color: #7e8792;
    border: 1px solid #282d34;
    border-radius: 5px;
    padding: 2px 6px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 700;
}

QLabel.panelTitle, QLabel.cardTitle {
    color: #eef0f2;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: -0.2px;
}

QLabel.panelSubtitle, QLabel.subText {
    color: #7e8792;
    font-size: 11px;
}

QLabel.eyebrowText {
    color: #7e8792;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Monospace Numbers & Metrics */
QLabel.monoValue, QLabel.metricValue {
    color: #eef0f2;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.6px;
}

QLabel.largeOffsetDisplay {
    color: #eef0f2;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -1px;
}

QLabel.metricUnit {
    color: #7e8792;
    font-size: 11px;
    font-weight: 500;
}

/* Micro-chips and Badges */
QLabel.systemChip, QLabel.badgeNeutral {
    background-color: #15181d;
    color: #c1c6cd;
    border: 1px solid #282d34;
    border-radius: 6px;
    padding: 3px 8px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 600;
}

QLabel.badgeSignal {
    background-color: rgba(217, 245, 107, 0.12);
    color: #d9f56b;
    border: 1px solid rgba(217, 245, 107, 0.35);
    border-radius: 6px;
    padding: 3px 8px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeGreen {
    background-color: rgba(188, 231, 160, 0.12);
    color: #bce7a0;
    border: 1px solid rgba(188, 231, 160, 0.35);
    border-radius: 6px;
    padding: 3px 8px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 600;
}

QLabel.badgeAmber {
    background-color: rgba(231, 199, 131, 0.12);
    color: #e7c783;
    border: 1px solid rgba(231, 199, 131, 0.35);
    border-radius: 6px;
    padding: 3px 8px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 600;
}

QLabel.codecChip {
    background-color: #191d22;
    color: #c1c6cd;
    border: 1px solid #282d34;
    border-radius: 4px;
    padding: 2px 6px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 600;
}

/* Buttons */
QPushButton.btnPrimary, QPushButton.btnRemuxSignal {
    background-color: #d9f56b;
    color: #15190b;
    border: 1px solid #d9f56b;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 750;
    font-size: 12px;
    letter-spacing: -0.1px;
}

QPushButton.btnPrimary:hover, QPushButton.btnRemuxSignal:hover {
    background-color: #e6f98c;
    border-color: #e6f98c;
}

QPushButton.btnPrimary:pressed, QPushButton.btnRemuxSignal:pressed {
    background-color: #c4e05b;
}

QPushButton.btnPrimary:disabled, QPushButton.btnRemuxSignal:disabled {
    background-color: #191d22;
    border-color: #282d34;
    color: #555d67;
}

QPushButton.btnSuccess {
    background-color: #d9f56b;
    color: #15190b;
    border: 1px solid #d9f56b;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 750;
    font-size: 12px;
}

QPushButton.btnSuccess:hover {
    background-color: #e6f98c;
}

QPushButton.btnSuccess:disabled {
    background-color: #191d22;
    border-color: #282d34;
    color: #555d67;
}

QPushButton.btnSecondary {
    background-color: #15181d;
    color: #c1c6cd;
    border: 1px solid #282d34;
    border-radius: 8px;
    padding: 6px 12px;
    font-weight: 600;
    font-size: 11px;
}

QPushButton.btnSecondary:hover {
    background-color: #191d22;
    border-color: #3b424c;
    color: #eef0f2;
}

QPushButton.btnSecondary:pressed {
    background-color: #0e1013;
}

QPushButton.btnNudge {
    background-color: #15181d;
    color: #c1c6cd;
    border: 1px solid #282d34;
    border-radius: 6px;
    padding: 5px 8px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    font-weight: 600;
}

QPushButton.btnNudge:hover {
    background-color: #191d22;
    border-color: #3b424c;
    color: #eef0f2;
}

QPushButton.btnDanger {
    background-color: rgba(231, 161, 155, 0.12);
    color: #e7a19b;
    border: 1px solid rgba(231, 161, 155, 0.35);
    border-radius: 8px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 11px;
}

QPushButton.btnDanger:hover {
    background-color: rgba(231, 161, 155, 0.22);
    border-color: #e7a19b;
}

/* Unified Drop Zone States */
QFrame#dropFrameEmpty {
    border: 1px dashed #3b424c;
    border-radius: 11px;
    background-color: #0e1013;
    padding: 20px;
}

QFrame#dropFrameEmpty:hover {
    border-color: #d9f56b;
    background-color: #111317;
}

QFrame#dropFrameSingle {
    border: 1px dashed #e7c783;
    border-radius: 11px;
    background-color: #111317;
    padding: 16px;
}

/* File Card Workbench */
QFrame.fileCardWorkbench {
    background-color: #0e1013;
    border: 1px solid #282d34;
    border-radius: 9px;
    padding: 10px 12px;
}

QFrame.fileCardWorkbench:hover {
    border-color: #3b424c;
}

/* Inputs & Comboboxes */
QLineEdit {
    background-color: #0e1013;
    color: #eef0f2;
    border: 1px solid #282d34;
    border-radius: 8px;
    padding: 7px 10px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
}

QLineEdit:focus {
    border-color: #d9f56b;
}

QComboBox {
    background-color: #15181d;
    color: #eef0f2;
    border: 1px solid #282d34;
    border-radius: 7px;
    padding: 6px 12px;
    font-size: 11px;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #3b424c;
}

QComboBox:focus {
    border-color: #d9f56b;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox QAbstractItemView {
    background-color: #15181d;
    color: #eef0f2;
    border: 1px solid #3b424c;
    selection-background-color: #191d22;
    selection-color: #d9f56b;
    padding: 4px;
}

/* Linear Offset Slider */
QSlider::groove:horizontal {
    height: 4px;
    background: #282d34;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #d9f56b;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #d9f56b;
    border: 2px solid #0a0b0d;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #ffffff;
}

/* Progress Bar */
QProgressBar {
    background-color: #0e1013;
    border: 1px solid #282d34;
    border-radius: 6px;
    height: 14px;
    text-align: center;
    color: #c1c6cd;
    font-family: 'SFMono-Regular', Consolas, monospace;
    font-size: 10px;
    font-weight: 600;
}

QProgressBar::chunk {
    background-color: #d9f56b;
    border-radius: 5px;
}

/* Checkboxes */
QCheckBox {
    color: #c1c6cd;
    font-size: 11px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #3b424c;
    border-radius: 4px;
    background-color: #0e1013;
}

QCheckBox::indicator:hover {
    border-color: #d9f56b;
}

QCheckBox::indicator:checked {
    background-color: #d9f56b;
    border-color: #d9f56b;
}

/* Retractable Collapsible Section Toggle */
QPushButton#collapsibleHeaderBtn {
    background-color: transparent;
    color: #c1c6cd;
    border: none;
    font-size: 12px;
    font-weight: 700;
    text-align: left;
    padding: 4px 0;
}

QPushButton#collapsibleHeaderBtn:hover {
    color: #d9f56b;
}

/* Terminal & Log Drawer */
QPlainTextEdit {
    background-color: #07080a;
    color: #c1c6cd;
    border: 1px solid #282d34;
    border-radius: 8px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    padding: 8px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #0a0b0d;
    width: 6px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #282d34;
    min-height: 24px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #3b424c;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Modals */
QDialog {
    background-color: #111317;
    color: #eef0f2;
}

QDialog#completionDialog {
    background-color: #111317;
    border: 1px solid #3b424c;
    border-radius: 12px;
}

#completionDialog QLabel#badgeSuccessGlyph {
    background-color: rgba(217, 245, 107, 0.15);
    color: #d9f56b;
    border: 1px solid rgba(217, 245, 107, 0.4);
    border-radius: 18px;
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
    font-size: 14px;
    font-weight: 800;
    font-family: 'SFMono-Regular', monospace;
}

#completionDialog QLabel#completionTitle {
    color: #eef0f2;
    font-size: 15px;
    font-weight: 700;
}

#completionDialog QLineEdit#outputBoxMonospace {
    background-color: #0e1013;
    color: #eef0f2;
    border: 1px solid #282d34;
    border-radius: 6px;
    padding: 7px 10px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
}
"""

# ==============================================================================
# Light Theme QSS (Secondary: #f2f3f1 base, #fbfcfa panels, #c1df50 signal accent)
# ==============================================================================
LIGHT_THEME_QSS = """
/* Global Window & Typography (Workbench Precision Light) */
QWidget {
    background-color: #f2f3f1;
    color: #191c1a;
    font-family: 'Inter', 'Segoe UI', 'Liberation Sans', -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #c1df50;
    selection-color: #1a2206;
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
    background-color: #e9ebe8;
    border-bottom: 1px solid #d9ddd7;
}

QLabel#brandTitle {
    color: #191c1a;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: -0.4px;
}

QLabel#brandSubtitle {
    color: #737c73;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.2px;
}

QLabel#topCrumb {
    color: #737c73;
    font-size: 12px;
    border-left: 1px solid #d9ddd7;
    padding-left: 14px;
}

QLabel#topCrumb strong {
    color: #424943;
    font-weight: 600;
}

/* Pipeline Stepper Bar */
QFrame#pipelineStepperFrame {
    background-color: #fbfcfa;
    border: 1px solid #d9ddd7;
    border-radius: 9px;
    padding: 3px;
}

QPushButton.pipeStepBtn {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 7px;
    color: #737c73;
    padding: 7px 12px;
    text-align: left;
    font-weight: 600;
    font-size: 11px;
}

QPushButton.pipeStepBtn:hover {
    background-color: #f1f3ef;
    color: #191c1a;
}

QPushButton.pipeStepBtn[active="true"] {
    background-color: #e8ebe6;
    border-color: #b9c0b7;
    color: #191c1a;
}

QPushButton.pipeStepBtn[done="true"] {
    background-color: transparent;
    color: #386d29;
}

/* Surface Panels and Cards */
QFrame.panelCard, QFrame.bentoCard {
    background-color: #fbfcfa;
    border: 1px solid #d9ddd7;
    border-radius: 12px;
}

QFrame.panelCard:hover, QFrame.bentoCard:hover {
    border-color: #b9c0b7;
}

/* Subcards / Inset Containers */
QFrame.subCard, QFrame.auditCard {
    background-color: #e9ebe8;
    border: 1px solid #d9ddd7;
    border-radius: 8px;
    padding: 10px;
}

/* Panel Header and Headings */
QWidget.panelHead {
    border-bottom: 1px solid #d9ddd7;
}

QLabel.sectionIndex {
    background-color: #f1f3ef;
    color: #737c73;
    border: 1px solid #d9ddd7;
    border-radius: 5px;
    padding: 2px 6px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 700;
}

QLabel.panelTitle, QLabel.cardTitle {
    color: #191c1a;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: -0.2px;
}

QLabel.panelSubtitle, QLabel.subText {
    color: #737c73;
    font-size: 11px;
}

QLabel.eyebrowText {
    color: #737c73;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Monospace Numbers & Metrics */
QLabel.monoValue, QLabel.metricValue {
    color: #191c1a;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.6px;
}

QLabel.largeOffsetDisplay {
    color: #191c1a;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -1px;
}

QLabel.metricUnit {
    color: #737c73;
    font-size: 11px;
    font-weight: 500;
}

/* Micro-chips and Badges */
QLabel.systemChip, QLabel.badgeNeutral {
    background-color: #f1f3ef;
    color: #424943;
    border: 1px solid #d9ddd7;
    border-radius: 6px;
    padding: 3px 8px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 600;
}

QLabel.badgeSignal {
    background-color: rgba(193, 223, 80, 0.2);
    color: #1a2206;
    border: 1px solid rgba(193, 223, 80, 0.6);
    border-radius: 6px;
    padding: 3px 8px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 700;
}

QLabel.badgeGreen {
    background-color: rgba(56, 109, 41, 0.12);
    color: #386d29;
    border: 1px solid rgba(56, 109, 41, 0.35);
    border-radius: 6px;
    padding: 3px 8px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 600;
}

QLabel.badgeAmber {
    background-color: rgba(148, 106, 25, 0.12);
    color: #946a19;
    border: 1px solid rgba(148, 106, 25, 0.35);
    border-radius: 6px;
    padding: 3px 8px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 600;
}

QLabel.codecChip {
    background-color: #e8ebe6;
    color: #424943;
    border: 1px solid #d9ddd7;
    border-radius: 4px;
    padding: 2px 6px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 10px;
    font-weight: 600;
}

/* Buttons */
QPushButton.btnPrimary, QPushButton.btnRemuxSignal {
    background-color: #c1df50;
    color: #1a2206;
    border: 1px solid #c1df50;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 750;
    font-size: 12px;
    letter-spacing: -0.1px;
}

QPushButton.btnPrimary:hover, QPushButton.btnRemuxSignal:hover {
    background-color: #ceea5e;
    border-color: #ceea5e;
}

QPushButton.btnPrimary:pressed, QPushButton.btnRemuxSignal:pressed {
    background-color: #b3d142;
}

QPushButton.btnPrimary:disabled, QPushButton.btnRemuxSignal:disabled {
    background-color: #e8ebe6;
    border-color: #d9ddd7;
    color: #99a198;
}

QPushButton.btnSuccess {
    background-color: #c1df50;
    color: #1a2206;
    border: 1px solid #c1df50;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 750;
    font-size: 12px;
}

QPushButton.btnSuccess:hover {
    background-color: #ceea5e;
}

QPushButton.btnSuccess:disabled {
    background-color: #e8ebe6;
    border-color: #d9ddd7;
    color: #99a198;
}

QPushButton.btnSecondary {
    background-color: #f1f3ef;
    color: #424943;
    border: 1px solid #d9ddd7;
    border-radius: 8px;
    padding: 6px 12px;
    font-weight: 600;
    font-size: 11px;
}

QPushButton.btnSecondary:hover {
    background-color: #e8ebe6;
    border-color: #b9c0b7;
    color: #191c1a;
}

QPushButton.btnSecondary:pressed {
    background-color: #dfe3dc;
}

QPushButton.btnNudge {
    background-color: #f1f3ef;
    color: #424943;
    border: 1px solid #d9ddd7;
    border-radius: 6px;
    padding: 5px 8px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    font-weight: 600;
}

QPushButton.btnNudge:hover {
    background-color: #e8ebe6;
    border-color: #b9c0b7;
    color: #191c1a;
}

QPushButton.btnDanger {
    background-color: rgba(157, 73, 65, 0.12);
    color: #9d4941;
    border: 1px solid rgba(157, 73, 65, 0.35);
    border-radius: 8px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 11px;
}

QPushButton.btnDanger:hover {
    background-color: rgba(157, 73, 65, 0.22);
    border-color: #9d4941;
}

/* Unified Drop Zone States */
QFrame#dropFrameEmpty {
    border: 1px dashed #b9c0b7;
    border-radius: 11px;
    background-color: #e9ebe8;
    padding: 20px;
}

QFrame#dropFrameEmpty:hover {
    border-color: #c1df50;
    background-color: #f1f3ef;
}

QFrame#dropFrameSingle {
    border: 1px dashed #946a19;
    border-radius: 11px;
    background-color: #f1f3ef;
    padding: 16px;
}

/* File Card Workbench */
QFrame.fileCardWorkbench {
    background-color: #e9ebe8;
    border: 1px solid #d9ddd7;
    border-radius: 9px;
    padding: 10px 12px;
}

QFrame.fileCardWorkbench:hover {
    border-color: #b9c0b7;
}

/* Inputs & Comboboxes */
QLineEdit {
    background-color: #fbfcfa;
    color: #191c1a;
    border: 1px solid #d9ddd7;
    border-radius: 8px;
    padding: 7px 10px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
}

QLineEdit:focus {
    border-color: #c1df50;
}

QComboBox {
    background-color: #f1f3ef;
    color: #191c1a;
    border: 1px solid #d9ddd7;
    border-radius: 7px;
    padding: 6px 12px;
    font-size: 11px;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #b9c0b7;
}

QComboBox:focus {
    border-color: #c1df50;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox QAbstractItemView {
    background-color: #fbfcfa;
    color: #191c1a;
    border: 1px solid #b9c0b7;
    selection-background-color: #e8ebe6;
    selection-color: #191c1a;
    padding: 4px;
}

/* Linear Offset Slider */
QSlider::groove:horizontal {
    height: 4px;
    background: #d9ddd7;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #c1df50;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #c1df50;
    border: 2px solid #f2f3f1;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #191c1a;
}

/* Progress Bar */
QProgressBar {
    background-color: #e9ebe8;
    border: 1px solid #d9ddd7;
    border-radius: 6px;
    height: 14px;
    text-align: center;
    color: #424943;
    font-family: 'SFMono-Regular', Consolas, monospace;
    font-size: 10px;
    font-weight: 600;
}

QProgressBar::chunk {
    background-color: #c1df50;
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
    border: 1px solid #b9c0b7;
    border-radius: 4px;
    background-color: #fbfcfa;
}

QCheckBox::indicator:hover {
    border-color: #c1df50;
}

QCheckBox::indicator:checked {
    background-color: #c1df50;
    border-color: #c1df50;
}

/* Retractable Collapsible Section Toggle */
QPushButton#collapsibleHeaderBtn {
    background-color: transparent;
    color: #424943;
    border: none;
    font-size: 12px;
    font-weight: 700;
    text-align: left;
    padding: 4px 0;
}

QPushButton#collapsibleHeaderBtn:hover {
    color: #191c1a;
}

/* Terminal & Log Drawer */
QPlainTextEdit {
    background-color: #e8ebe6;
    color: #191c1a;
    border: 1px solid #d9ddd7;
    border-radius: 8px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
    padding: 8px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #f2f3f1;
    width: 6px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #d9ddd7;
    min-height: 24px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #b9c0b7;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Modals */
QDialog {
    background-color: #fbfcfa;
    color: #191c1a;
}

QDialog#completionDialog {
    background-color: #fbfcfa;
    border: 1px solid #b9c0b7;
    border-radius: 12px;
}

#completionDialog QLabel#badgeSuccessGlyph {
    background-color: rgba(193, 223, 80, 0.2);
    color: #1a2206;
    border: 1px solid rgba(193, 223, 80, 0.6);
    border-radius: 18px;
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
    font-size: 14px;
    font-weight: 800;
    font-family: 'SFMono-Regular', monospace;
}

#completionDialog QLabel#completionTitle {
    color: #191c1a;
    font-size: 15px;
    font-weight: 700;
}

#completionDialog QLineEdit#outputBoxMonospace {
    background-color: #e9ebe8;
    color: #191c1a;
    border: 1px solid #d9ddd7;
    border-radius: 6px;
    padding: 7px 10px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
    font-size: 11px;
}
"""


def get_theme_stylesheet(mode: Literal["dark", "light"] = "dark") -> str:
    """Returns the QSS stylesheet for the requested precision bench theme."""
    return DARK_THEME_QSS if mode == "dark" else LIGHT_THEME_QSS


def get_theme_qss(mode: Literal["dark", "light"] = "dark") -> str:
    """Backwards-compatible alias for get_theme_stylesheet."""
    return get_theme_stylesheet(mode)


def apply_workbench_theme(widget, mode: Literal["dark", "light"] = "dark"):
    """Applies the precision bench theme to the target application or widget."""
    widget.setStyleSheet(get_theme_stylesheet(mode))


def apply_theme(target_widget, mode: Literal["dark", "light"] = "dark"):
    """Backwards-compatible alias for apply_workbench_theme."""
    apply_workbench_theme(target_widget, mode)
