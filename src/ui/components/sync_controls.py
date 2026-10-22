"""Offset fine-tuning controls and synchronization metrics panel."""

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
    Panel providing manual offset adjustments (±50ms steps, fast jumps, slider)
    and metric status badges (drift ratio, confidence, FPS diagnostic).
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
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header with Metrics and Recalculate Button
        header_layout = QHBoxLayout()
        title = QLabel("Alinhamento Temporal & Métricas")
        title.setProperty("class", "cardTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Metrics Display Grid
        grid = QGridLayout()
        grid.setSpacing(10)

        # Metric: Static Offset
        lbl_offset_title = QLabel("Offset Estático:")
        lbl_offset_title.setProperty("class", "subText")
        grid.addWidget(lbl_offset_title, 0, 0)

        self.lbl_offset_val = QLabel("0.0 ms")
        self.lbl_offset_val.setProperty("class", "metricValue")
        grid.addWidget(self.lbl_offset_val, 1, 0)

        # Metric: Drift Ratio
        lbl_drift_title = QLabel("Deriva Temporal (Drift):")
        lbl_drift_title.setProperty("class", "subText")
        grid.addWidget(lbl_drift_title, 0, 1)

        self.lbl_drift_val = QLabel("1.000000x")
        self.lbl_drift_val.setStyleSheet("font-family: 'JetBrains Mono', monospace; font-size: 15px; font-weight: 700;")
        grid.addWidget(self.lbl_drift_val, 1, 1)

        # Metric: Confidence
        lbl_conf_title = QLabel("Confiança Algorítmica:")
        lbl_conf_title.setProperty("class", "subText")
        grid.addWidget(lbl_conf_title, 0, 2)

        self.lbl_confidence = QLabel("Não analisado")
        self.lbl_confidence.setProperty("class", "badgeAmber")
        grid.addWidget(self.lbl_confidence, 1, 2)

        layout.addLayout(grid)

        # FPS Diagnostic banner
        self.lbl_diagnosis = QLabel("Taxas de quadros congruentes (sem deriva contínua)")
        self.lbl_diagnosis.setProperty("class", "badgeNeutral")
        self.lbl_diagnosis.setStyleSheet("padding: 6px 10px; font-size: 11px;")
        layout.addWidget(self.lbl_diagnosis)

        # Fine-Tuning Controls Row
        ctrl_box = QVBoxLayout()
        ctrl_box.setSpacing(8)

        lbl_tune = QLabel("Ajuste Fino Manual (Passos de ±50 ms):")
        lbl_tune.setStyleSheet("color: #d4d4d4; font-weight: 600; font-size: 12px;")
        ctrl_box.addWidget(lbl_tune)

        adj_row = QHBoxLayout()
        adj_row.setSpacing(8)

        # Quick step buttons
        btn_m250 = QPushButton("-250 ms")
        btn_m250.setProperty("class", "btnSecondary")
        btn_m250.clicked.connect(lambda: self.add_offset(-250.0))
        adj_row.addWidget(btn_m250)

        btn_m50 = QPushButton("-50 ms")
        btn_m50.setProperty("class", "btnSecondary")
        btn_m50.clicked.connect(lambda: self.add_offset(-50.0))
        adj_row.addWidget(btn_m50)

        # Spinbox
        self.spin_offset = QDoubleSpinBox()
        self.spin_offset.setRange(-60000.0, 60000.0)
        self.spin_offset.setSingleStep(50.0)
        self.spin_offset.setDecimals(1)
        self.spin_offset.setSuffix(" ms")
        self.spin_offset.valueChanged.connect(self._on_spin_changed)
        self.spin_offset.setFixedWidth(130)
        adj_row.addWidget(self.spin_offset)

        btn_p50 = QPushButton("+50 ms")
        btn_p50.setProperty("class", "btnSecondary")
        btn_p50.clicked.connect(lambda: self.add_offset(50.0))
        adj_row.addWidget(btn_p50)

        btn_p250 = QPushButton("+250 ms")
        btn_p250.setProperty("class", "btnSecondary")
        btn_p250.clicked.connect(lambda: self.add_offset(250.0))
        adj_row.addWidget(btn_p250)

        # Reset button
        self.btn_reset = QPushButton("Resetar")
        self.btn_reset.setProperty("class", "btnSecondary")
        self.btn_reset.clicked.connect(self.reset_to_calculated)
        adj_row.addWidget(self.btn_reset)

        ctrl_box.addLayout(adj_row)

        # Interactive Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(-5000, 5000)
        self.slider.setSingleStep(50)
        self.slider.setPageStep(250)
        self.slider.valueChanged.connect(self._on_slider_changed)
        ctrl_box.addWidget(self.slider)

        layout.addLayout(ctrl_box)

    def set_metrics(self, metrics: SyncMetrics):
        self.algorithmic_offset = metrics.static_offset_ms
        self.current_offset = metrics.static_offset_ms

        self.lbl_offset_val.setText(f"{metrics.static_offset_ms:+.1f} ms")
        self.lbl_drift_val.setText(f"{metrics.drift_ratio:.6f}x")
        self.lbl_diagnosis.setText(metrics.fps_diagnosis)

        pct = metrics.confidence_score * 100.0
        if metrics.is_confident:
            self.lbl_confidence.setText(f"Alta ({pct:.1f}%)")
            self.lbl_confidence.setProperty("class", "badgeGreen")
        else:
            self.lbl_confidence.setText(f"Baixa ({pct:.1f}%) — Ajuste Manual")
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
        self.lbl_offset_val.setText(f"{val:+.1f} ms")
        self.slider.blockSignals(True)
        self.slider.setValue(int(max(-5000, min(5000, round(val)))))
        self.slider.blockSignals(False)
        self.offset_changed.emit(val)

    def _on_slider_changed(self, val: int):
        self.current_offset = float(val)
        self.lbl_offset_val.setText(f"{float(val):+.1f} ms")
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
        self.lbl_offset_val.setText("0.0 ms")
        self.lbl_drift_val.setText("1.000000x")
        self.lbl_confidence.setText("Não analisado")
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
