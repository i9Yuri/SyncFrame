"""Offset fine-tuning controls and synchronization metrics panel for Workbench."""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget
)

from ...core.models import SyncMetrics


class SyncControls(QFrame):
    """
    Panel providing manual offset adjustments (large monospace display, slider, nudge buttons)
    and metric status badges (drift ratio, confidence, FPS diagnostic) adhering to Precision Bench.
    """
    offset_changed = Signal(float)
    analyze_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("bentoCard")
        self.setProperty("class", "bentoCard")

        self.algorithmic_offset: float = 0.0
        self.current_offset: float = 0.0

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 16, 18, 16)

        # Header with Title and Section Index
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        idx_badge = QLabel("03A")
        idx_badge.setProperty("class", "sectionIndex")
        header_layout.addWidget(idx_badge)

        title = QLabel("Alinhamento Temporal & Métricas")
        title.setProperty("class", "cardTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.chip_track = QLabel("TRACK A02")
        self.chip_track.setProperty("class", "badgeSignal")
        header_layout.addWidget(self.chip_track)
        layout.addLayout(header_layout)

        # Large Monospace Offset Display Area
        disp_box = QHBoxLayout()
        disp_box.setSpacing(12)

        disp_sub = QVBoxLayout()
        disp_sub.setSpacing(2)
        lbl_sub = QLabel("AUDIO OFFSET / STATIC SYNC")
        lbl_sub.setProperty("class", "eyebrowText")
        disp_sub.addWidget(lbl_sub)

        self.lbl_offset_val = QLabel("+0.0 ms")
        self.lbl_offset_val.setProperty("class", "largeOffsetDisplay")
        disp_sub.addWidget(self.lbl_offset_val)
        disp_box.addLayout(disp_sub)

        disp_box.addStretch()

        self.btn_reset = QPushButton("Resetar")
        self.btn_reset.setProperty("class", "btnSecondary")
        self.btn_reset.clicked.connect(self.reset_to_calculated)
        disp_box.addWidget(self.btn_reset, alignment=Qt.AlignVCenter)
        layout.addLayout(disp_box)

        # Interactive Slider with range labels
        slider_box = QVBoxLayout()
        slider_box.setSpacing(4)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(-5000, 5000)
        self.slider.setSingleStep(1)
        self.slider.setPageStep(50)
        self.slider.valueChanged.connect(self._on_slider_changed)
        slider_box.addWidget(self.slider)

        lbl_row = QHBoxLayout()
        lbl_left = QLabel("-5000 ms")
        lbl_left.setProperty("class", "subText")
        lbl_mid = QLabel("0")
        lbl_mid.setProperty("class", "subText")
        lbl_right = QLabel("+5000 ms")
        lbl_right.setProperty("class", "subText")
        lbl_row.addWidget(lbl_left)
        lbl_row.addStretch()
        lbl_row.addWidget(lbl_mid)
        lbl_row.addStretch()
        lbl_row.addWidget(lbl_right)
        slider_box.addLayout(lbl_row)
        layout.addLayout(slider_box)

        # Precision Nudge Grid (±1, ±10, ±50, ±250 ms)
        nudge_layout = QHBoxLayout()
        nudge_layout.setSpacing(6)

        for val, txt in [
            (-250.0, "-250 ms"),
            (-50.0, "-50 ms"),
            (-10.0, "-10 ms"),
            (-1.0, "-1 ms"),
            (1.0, "+1 ms"),
            (10.0, "+10 ms"),
            (50.0, "+50 ms"),
            (250.0, "+250 ms"),
        ]:
            btn = QPushButton(txt)
            btn.setProperty("class", "btnNudge")
            btn.clicked.connect(lambda _, d=val: self.add_offset(d))
            nudge_layout.addWidget(btn)

        layout.addLayout(nudge_layout)

        # Hidden Spinbox for compatibility with unit tests
        self.spin_offset = QDoubleSpinBox()
        self.spin_offset.setRange(-60000.0, 60000.0)
        self.spin_offset.setSingleStep(50.0)
        self.spin_offset.setDecimals(1)
        self.spin_offset.setSuffix(" ms")
        self.spin_offset.valueChanged.connect(self._on_spin_changed)
        self.spin_offset.setVisible(False)
        layout.addWidget(self.spin_offset)

        # Separator Line
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #282d34; height: 1px; border: none;")
        layout.addWidget(sep)

        # Metrics Display Grid
        grid = QGridLayout()
        grid.setSpacing(8)

        # Metric: Drift Ratio
        box_drift = QFrame()
        box_drift.setProperty("class", "subCard")
        bd_layout = QVBoxLayout(box_drift)
        bd_layout.setContentsMargins(8, 8, 8, 8)
        lbl_drift_title = QLabel("DERIVA TEMPORAL")
        lbl_drift_title.setProperty("class", "eyebrowText")
        bd_layout.addWidget(lbl_drift_title)
        self.lbl_drift_val = QLabel("1.000000x")
        self.lbl_drift_val.setProperty("class", "monoValue")
        bd_layout.addWidget(self.lbl_drift_val)
        grid.addWidget(box_drift, 0, 0)

        # Metric: Confidence
        box_conf = QFrame()
        box_conf.setProperty("class", "subCard")
        bc_layout = QVBoxLayout(box_conf)
        bc_layout.setContentsMargins(8, 8, 8, 8)
        lbl_conf_title = QLabel("CONFIANCA FFT")
        lbl_conf_title.setProperty("class", "eyebrowText")
        bc_layout.addWidget(lbl_conf_title)
        self.lbl_confidence = QLabel("Nao analisado")
        self.lbl_confidence.setProperty("class", "badgeAmber")
        bc_layout.addWidget(self.lbl_confidence)
        grid.addWidget(box_conf, 0, 1)

        layout.addLayout(grid)

        # FPS Diagnostic banner
        self.lbl_diagnosis = QLabel("Taxas de quadros congruentes (sem deriva contínua)")
        self.lbl_diagnosis.setProperty("class", "badgeNeutral")
        self.lbl_diagnosis.setStyleSheet("padding: 6px 10px; font-size: 11px;")
        layout.addWidget(self.lbl_diagnosis)

    def set_metrics(self, metrics: SyncMetrics):
        self.algorithmic_offset = metrics.static_offset_ms
        self.current_offset = metrics.static_offset_ms

        sign = "+" if metrics.static_offset_ms >= 0 else ""
        self.lbl_offset_val.setText(f"{sign}{metrics.static_offset_ms:.1f} ms")
        self.lbl_drift_val.setText(f"{metrics.drift_ratio:.6f}x")
        self.lbl_diagnosis.setText(metrics.fps_diagnosis)

        pct = metrics.confidence_score * 100.0
        if metrics.is_confident:
            self.lbl_confidence.setText(f"Alta ({pct:.1f}%)")
            self.lbl_confidence.setProperty("class", "badgeGreen")
        else:
            self.lbl_confidence.setText(f"Baixa ({pct:.1f}%) — Manual")
            self.lbl_confidence.setProperty("class", "badgeAmber")
        self.lbl_confidence.setStyle(self.lbl_confidence.style())

        self.spin_offset.blockSignals(True)
        self.spin_offset.setValue(metrics.static_offset_ms)
        self.spin_offset.blockSignals(False)

        self.slider.blockSignals(True)
        clamped_val = int(max(-5000, min(5000, round(metrics.static_offset_ms))))
        self.slider.setValue(clamped_val)
        self.slider.blockSignals(False)

    def _on_spin_changed(self, val: float):
        self.current_offset = val
        sign = "+" if val >= 0 else ""
        self.lbl_offset_val.setText(f"{sign}{val:.1f} ms")
        self.slider.blockSignals(True)
        self.slider.setValue(int(max(-5000, min(5000, round(val)))))
        self.slider.blockSignals(False)
        self.offset_changed.emit(val)

    def _on_slider_changed(self, val: int):
        self.current_offset = float(val)
        sign = "+" if val >= 0 else ""
        self.lbl_offset_val.setText(f"{sign}{float(val):.1f} ms")
        self.spin_offset.blockSignals(True)
        self.spin_offset.setValue(float(val))
        self.spin_offset.blockSignals(False)
        self.offset_changed.emit(float(val))

    def add_offset(self, delta_ms: float):
        new_val = self.current_offset + delta_ms
        self.spin_offset.setValue(new_val)

    def reset_to_calculated(self):
        self.spin_offset.setValue(self.algorithmic_offset)

    def reset(self):
        """Resets all metrics and adjustment inputs to initial state."""
        self.algorithmic_offset = 0.0
        self.current_offset = 0.0
        self.lbl_offset_val.setText("+0.0 ms")
        self.lbl_drift_val.setText("1.000000x")
        self.lbl_confidence.setText("Nao analisado")
        self.lbl_confidence.setProperty("class", "badgeAmber")
        self.lbl_confidence.setStyle(self.lbl_confidence.style())
        self.lbl_diagnosis.setText("Taxas de quadros congruentes (sem deriva contínua)")
        self.spin_offset.blockSignals(True)
        self.spin_offset.setValue(0.0)
        self.spin_offset.blockSignals(False)
        self.slider.blockSignals(True)
        self.slider.setValue(0)
        self.slider.blockSignals(False)

    def get_offset_ms(self) -> float:
        return self.spin_offset.value()
