"""Pro Max v4 QSS Stylesheet for SyncFrame."""

DARK_THEME_QSS = """
/* Global Window & Fonts */
QWidget {
    background-color: #090d16;
    color: #f1f5f9;
    font-family: 'Inter', 'Cantarell', 'Segoe UI', system-ui, sans-serif;
    font-size: 13px;
    selection-background-color: #0891b2;
    selection-color: #ffffff;
}

/* Bento Cards / Group Containers */
QFrame.bentoCard {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 12px;
}

QFrame.bentoCard:hover {
    border-color: #334155;
}

QFrame.bentoHighlight {
    background-color: #0f172a;
    border: 1px solid #0891b2;
    border-radius: 10px;
}

/* Headings */
QLabel.cardTitle {
    color: #38bdf8;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: -0.3px;
}

QLabel.metricValue {
    color: #22d3ee;
    font-family: 'JetBrains Mono', 'Fira Code', 'DejaVu Sans Mono', monospace;
    font-size: 20px;
    font-weight: 800;
}

QLabel.subText {
    color: #94a3b8;
    font-size: 11px;
}

QLabel.badgeGreen {
    background-color: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.4);
    border-radius: 6px;
    padding: 3px 8px;
    font-weight: 600;
    font-size: 11px;
}

QLabel.badgeAmber {
    background-color: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.4);
    border-radius: 6px;
    padding: 3px 8px;
    font-weight: 600;
    font-size: 11px;
}

QLabel.badgeBlue {
    background-color: rgba(14, 165, 233, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(14, 165, 233, 0.4);
    border-radius: 6px;
    padding: 3px 8px;
    font-weight: 600;
    font-size: 11px;
}

/* Primary Action Buttons */
QPushButton.btnPrimary {
    background-color: #0891b2;
    color: #ffffff;
    border: 1px solid #06b6d4;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 700;
    font-size: 13px;
}

QPushButton.btnPrimary:hover {
    background-color: #06b6d4;
    border-color: #22d3ee;
}

QPushButton.btnPrimary:pressed {
    background-color: #0e7490;
}

QPushButton.btnPrimary:disabled {
    background-color: #1e293b;
    border-color: #334155;
    color: #64748b;
}

/* Secondary Action Buttons */
QPushButton.btnSecondary {
    background-color: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px 14px;
    font-weight: 600;
}

QPushButton.btnSecondary:hover {
    background-color: #334155;
    border-color: #475569;
    color: #ffffff;
}

QPushButton.btnSecondary:pressed {
    background-color: #0f172a;
}

/* Success / Remux Button */
QPushButton.btnSuccess {
    background-color: #059669;
    color: #ffffff;
    border: 1px solid #10b981;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 700;
    font-size: 14px;
}

QPushButton.btnSuccess:hover {
    background-color: #10b981;
    border-color: #34d399;
}

QPushButton.btnSuccess:disabled {
    background-color: #1e293b;
    border-color: #334155;
    color: #64748b;
}

/* Danger / Abort Button */
QPushButton.btnDanger {
    background-color: rgba(239, 68, 68, 0.2);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.4);
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton.btnDanger:hover {
    background-color: #dc2626;
    color: #ffffff;
}

/* Form Inputs & Dropdowns */
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #020617;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    font-family: 'JetBrains Mono', 'Fira Code', 'DejaVu Sans Mono', monospace;
    font-size: 13px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #22d3ee;
}

QComboBox {
    background-color: #020617;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    min-width: 140px;
}

QComboBox:hover {
    border-color: #475569;
}

QComboBox:focus {
    border-color: #22d3ee;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #0f172a;
    border: 1px solid #334155;
    color: #f8fafc;
    selection-background-color: #0891b2;
    selection-color: #ffffff;
    padding: 4px;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 6px;
    background: #1e293b;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #0891b2;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #22d3ee;
    border: 2px solid #0e7490;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #38bdf8;
}

/* Progress Bar */
QProgressBar {
    background-color: #020617;
    border: 1px solid #1e293b;
    border-radius: 6px;
    height: 14px;
    text-align: center;
    color: #f8fafc;
    font-size: 11px;
    font-weight: 600;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0891b2, stop:1 #10b981);
    border-radius: 5px;
}

/* Checkbox */
QCheckBox {
    color: #cbd5e1;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    background-color: #020617;
    border: 1px solid #334155;
    border-radius: 4px;
}

QCheckBox::indicator:hover {
    border-color: #22d3ee;
}

QCheckBox::indicator:checked {
    background-color: #0891b2;
    border-color: #06b6d4;
    image: none;
}

/* Log and Text Areas */
QPlainTextEdit, QTextEdit {
    background-color: #020617;
    color: #94a3b8;
    border: 1px solid #1e293b;
    border-radius: 6px;
    font-family: 'JetBrains Mono', 'Fira Code', 'DejaVu Sans Mono', monospace;
    font-size: 11px;
    padding: 8px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #090d16;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: #090d16;
    height: 8px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #334155;
    min-width: 24px;
    border-radius: 4px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""
