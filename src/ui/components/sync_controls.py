"""Offset fine-tuning controls and synchronization metrics panel for Workbench."""

from typing import Any, Callable, Dict, Literal, Optional

from PySide6.QtCore import QPoint, Qt, Signal
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


class SliderSensitivityController:
    """Manages granularity and step sensitivity resolution for the temporal alignment slider."""

    def __init__(self, slider: QSlider, on_changed: Optional[Callable[["SliderSensitivityController"], None]] = None):
        self.mode: Literal["fine", "normal", "coarse"] = "normal"
        self.step_ms: int = 10
        self.scale_factor: float = 1.0
        self.slider = slider
        self.on_changed = on_changed
        self._apply_mode()

    def set_mode(self, mode: Literal["fine", "normal", "coarse"]) -> None:
        self.mode = mode
        if mode == "fine":
            self.step_ms = 1
            self.scale_factor = 0.25
        elif mode == "normal":
            self.step_ms = 10
            self.scale_factor = 1.0
        elif mode == "coarse":
            self.step_ms = 50
            self.scale_factor = 2.5
        self._apply_mode()
        if self.on_changed:
            self.on_changed(self)

    def _apply_mode(self) -> None:
        if self.slider:
            self.slider.setSingleStep(self.step_ms)
            if hasattr(self.slider, "step_ms"):
                self.slider.step_ms = self.step_ms
            if hasattr(self.slider, "scale_factor"):
                self.slider.scale_factor = self.scale_factor

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "step_ms": self.step_ms,
            "scale_factor": self.scale_factor,
        }

    def __getitem__(self, item: str):
        return getattr(self, item)


class DampedSlider(QSlider):
    """
    Precision horizontal slider with amortized dragging physics:
    - Filters raw cursor jumps via fractional scale factor
    - Rounds steps deterministically to current sensitivity granularity (1ms / 10ms / 50ms)
    - Pure white spherical thumb handle with zero visual artifacts
    """
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.step_ms: int = 10
        self.scale_factor: float = 1.0
        self._drag_start_pos: Optional[QPoint] = None
        self._drag_start_val: Optional[int] = None

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._drag_start_pos = ev.pos()
            self._drag_start_val = self.value()
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self._drag_start_pos is not None and (ev.buttons() & Qt.LeftButton):
            dx = ev.pos().x() - self._drag_start_pos.x()
            track_w = max(1, self.width() - 20)
            val_range = self.maximum() - self.minimum()
            fractional_delta = (dx / float(track_w)) * val_range * self.scale_factor
            stepped_delta = round(fractional_delta / float(self.step_ms)) * self.step_ms
            new_val = int(max(self.minimum(), min(self.maximum(), self._drag_start_val + stepped_delta)))
            if new_val != self.value():
                self.setValue(new_val)
            ev.accept()
        else:
            super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        self._drag_start_pos = None
        self._drag_start_val = None
        super().mouseReleaseEvent(ev)


class SyncControls(QFrame):
    """
    Panel providing manual offset adjustments (large monospace display, slider, nudge buttons)
    and metric status badges (drift ratio, confidence, FPS diagnostic) adhering to One UI 8.5.
    """
    offset_changed = Signal(float)
    analyze_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("bentoCard")
        self.setProperty("class", "card")

        self.algorithmic_offset: float = 0.0
        self.current_offset: float = 0.0

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(18, 16, 18, 16)

        # Header with Title and Track Tag
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.idx_badge = QLabel("03A")
        self.idx_badge.setVisible(False)
        header_layout.addWidget(self.idx_badge)

        title = QLabel("Alinhamento temporal")
        title.setProperty("class", "cardHeaderTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Precision Stepper: Pill segmented group (1 ms, 10 ms, 50 ms)
        self.stepper_group = QFrame()
        self.stepper_group.setObjectName("stepperGroup")
        self.stepper_group.setProperty("class", "pillSoft")
        sg_layout = QHBoxLayout(self.stepper_group)
        sg_layout.setContentsMargins(4, 2, 4, 2)
        sg_layout.setSpacing(4)

        self.btn_sens_fine = QPushButton("1 ms")
        self.btn_sens_fine.setProperty("class", "pill")
        self.btn_sens_fine.setToolTip("Resolução Fina (passos de 1 ms)")
        self.btn_sens_fine.clicked.connect(lambda: self.set_sensitivity_mode("fine"))
        sg_layout.addWidget(self.btn_sens_fine)

        self.btn_sens_normal = QPushButton("10 ms")
        self.btn_sens_normal.setProperty("class", "pill")
        self.btn_sens_normal.setToolTip("Resolução Normal (passos de 10 ms)")
        self.btn_sens_normal.clicked.connect(lambda: self.set_sensitivity_mode("normal"))
        sg_layout.addWidget(self.btn_sens_normal)

        self.btn_sens_coarse = QPushButton("50 ms")
        self.btn_sens_coarse.setProperty("class", "pill")
        self.btn_sens_coarse.setToolTip("Resolução Ampla (passos de 50 ms)")
        self.btn_sens_coarse.clicked.connect(lambda: self.set_sensitivity_mode("coarse"))
        sg_layout.addWidget(self.btn_sens_coarse)

        header_layout.addWidget(self.stepper_group)

        self.chip_track = QLabel("Faixa A02")
        self.chip_track.setObjectName("chipTrack")
        self.chip_track.setProperty("class", "statusPill")
        header_layout.addWidget(self.chip_track)
        layout.addLayout(header_layout)

        # Large Offset Display Area wrapped in offBox frame (.off)
        offset_callout_frame = QFrame()
        offset_callout_frame.setProperty("class", "offBox")
        disp_box = QHBoxLayout(offset_callout_frame)
        disp_box.setContentsMargins(18, 10, 14, 10)
        disp_box.setSpacing(12)

        disp_sub = QVBoxLayout()
        disp_sub.setSpacing(4)
        lbl_sub = QLabel("Offset de áudio · sincronia estática")
        lbl_sub.setProperty("class", "hint")
        disp_sub.addWidget(lbl_sub)

        self.lbl_offset_val = QLabel("+0,0 ms")
        self.lbl_offset_val.setProperty("class", "largeOffsetDisplay")
        disp_sub.addWidget(self.lbl_offset_val)
        disp_box.addLayout(disp_sub)

        disp_box.addStretch()

        self.btn_reset = QPushButton("Resetar")
        self.btn_reset.setProperty("class", "btn")
        self.btn_reset.clicked.connect(self.reset_to_calculated)
        disp_box.addWidget(self.btn_reset, alignment=Qt.AlignVCenter)
        layout.addWidget(offset_callout_frame)

        # Interactive Slider with range labels (.sl)
        self.frame_slider = QFrame()
        self.frame_slider.setObjectName("frameSlider")
        self.frame_slider.setProperty("class", "sliderContainer")
        slider_box = QVBoxLayout(self.frame_slider)
        slider_box.setContentsMargins(14, 10, 14, 10)
        slider_box.setSpacing(6)

        self.slider = DampedSlider(Qt.Horizontal)
        self.slider.setRange(-5000, 5000)
        self.slider.setSingleStep(10)
        self.slider.setPageStep(50)
        self.sensitivity_controller = SliderSensitivityController(self.slider)
        self.set_sensitivity_mode("normal")
        self.slider.valueChanged.connect(self._on_slider_changed)
        slider_box.addWidget(self.slider)

        lbl_row = QHBoxLayout()
        lbl_left = QLabel("−5000 ms")
        lbl_left.setProperty("class", "hint")
        lbl_mid = QLabel("0")
        lbl_mid.setProperty("class", "hint")
        lbl_right = QLabel("+5000 ms")
        lbl_right.setProperty("class", "hint")
        lbl_row.addWidget(lbl_left)
        lbl_row.addStretch()
        lbl_row.addWidget(lbl_mid)
        lbl_row.addStretch()
        lbl_row.addWidget(lbl_right)
        slider_box.addLayout(lbl_row)
        layout.addWidget(self.frame_slider)

        # Precision Nudge Grid: 2 rows of 4 buttons (.steps)
        grid_steps = QGridLayout()
        grid_steps.setSpacing(6)

        step_values = [
            (-250.0, "−250 ms", 0, 0),
            (-50.0, "−50 ms", 0, 1),
            (-10.0, "−10 ms", 0, 2),
            (-1.0, "−1 ms", 0, 3),
            (1.0, "+1 ms", 1, 0),
            (10.0, "+10 ms", 1, 1),
            (50.0, "+50 ms", 1, 2),
            (250.0, "+250 ms", 1, 3),
        ]

        for val, txt, r, c in step_values:
            btn = QPushButton(txt)
            btn.setProperty("class", "stepBtn")
            btn.clicked.connect(lambda _, d=val: self.add_offset(d))
            grid_steps.addWidget(btn, r, c)

        layout.addLayout(grid_steps)

        # Hidden Spinbox for compatibility with unit tests
        self.spin_offset = QDoubleSpinBox()
        self.spin_offset.setRange(-60000.0, 60000.0)
        self.spin_offset.setSingleStep(50.0)
        self.spin_offset.setDecimals(1)
        self.spin_offset.setSuffix(" ms")
        self.spin_offset.valueChanged.connect(self._on_spin_changed)
        self.spin_offset.setVisible(False)
        layout.addWidget(self.spin_offset)

        # Metrics Display Grid (.mets: 2 rounded boxes side-by-side)
        row_mets = QHBoxLayout()
        row_mets.setSpacing(8)

        # Metric: Drift Ratio
        box_drift = QFrame()
        box_drift.setProperty("class", "metBox")
        bd_layout = QVBoxLayout(box_drift)
        bd_layout.setContentsMargins(18, 14, 18, 14)
        bd_layout.setSpacing(4)
        lbl_drift_title = QLabel("Deriva temporal")
        lbl_drift_title.setProperty("class", "hint")
        bd_layout.addWidget(lbl_drift_title)
        self.lbl_drift_val = QLabel("1,000000x")
        self.lbl_drift_val.setProperty("class", "metVal")
        bd_layout.addWidget(self.lbl_drift_val)
        row_mets.addWidget(box_drift, 1)

        # Metric: Confidence & PSLR
        box_conf = QFrame()
        box_conf.setProperty("class", "metBox")
        bc_layout = QVBoxLayout(box_conf)
        bc_layout.setContentsMargins(18, 14, 18, 14)
        bc_layout.setSpacing(4)
        lbl_conf_title = QLabel("Confiança FFT / PSLR")
        lbl_conf_title.setProperty("class", "hint")
        bc_layout.addWidget(lbl_conf_title)
        self.lbl_confidence = QLabel("Não analisado")
        self.lbl_confidence.setProperty("class", "metVal")
        bc_layout.addWidget(self.lbl_confidence)
        row_mets.addWidget(box_conf, 1)

        layout.addLayout(row_mets)

        # Discontinuity Warning Banner (Cuts/Step Discontinuities)
        self.frame_discont = QFrame()
        self.frame_discont.setProperty("class", "dubBox")
        fd_layout = QVBoxLayout(self.frame_discont)
        fd_layout.setContentsMargins(14, 10, 14, 10)
        self.lbl_discont_title = QLabel("AVISO: DESCONTINUIDADE EM DEGRAU (CORTE/LOGO)")
        self.lbl_discont_title.setProperty("class", "dubTitle")
        fd_layout.addWidget(self.lbl_discont_title)
        self.lbl_discont_msg = QLabel("")
        self.lbl_discont_msg.setProperty("class", "dubDesc")
        self.lbl_discont_msg.setWordWrap(True)
        fd_layout.addWidget(self.lbl_discont_msg)
        self.frame_discont.setVisible(False)
        layout.addWidget(self.frame_discont)

        # Note pill (.note)
        self.frame_note = QFrame()
        self.frame_note.setProperty("class", "notePill")
        fn_layout = QHBoxLayout(self.frame_note)
        fn_layout.setContentsMargins(18, 10, 18, 10)
        fn_layout.setSpacing(8)

        dot = QLabel()
        dot.setProperty("class", "greenDot")
        dot.setFixedSize(8, 8)
        fn_layout.addWidget(dot)

        self.lbl_diagnosis = QLabel("Taxas de quadros congruentes (sem deriva contínua)")
        self.lbl_diagnosis.setProperty("class", "hint")
        fn_layout.addWidget(self.lbl_diagnosis)
        fn_layout.addStretch()
        layout.addWidget(self.frame_note)

    def set_metrics(self, metrics: SyncMetrics):
        self.algorithmic_offset = metrics.static_offset_ms
        self.current_offset = metrics.static_offset_ms

        sign = "+" if metrics.static_offset_ms >= 0 else "−"
        val_str = f"{abs(metrics.static_offset_ms):.1f}".replace(".", ",")
        self.lbl_offset_val.setText(f"{sign}{val_str} ms")
        self.lbl_drift_val.setText(f"{metrics.drift_ratio:.6f}x".replace(".", ","))
        self.lbl_diagnosis.setText(metrics.fps_diagnosis)

        # Check for non-linear step cuts
        if metrics.discontinuity_report and metrics.discontinuity_report.has_cuts:
            self.lbl_discont_msg.setText(metrics.discontinuity_report.diagnosis)
            self.frame_discont.setVisible(True)
        else:
            self.frame_discont.setVisible(False)

        pct = metrics.confidence_score * 100.0
        pslr_tag = f" • PSLR {metrics.pslr_score:.1f}".replace(".", ",") if metrics.pslr_score > 0 else ""
        if metrics.is_confident:
            self.lbl_confidence.setText(f"Alta ({pct:.1f}%{pslr_tag})".replace(".", ","))
        else:
            self.lbl_confidence.setText(f"Baixa ({pct:.1f}%{pslr_tag}) — Manual".replace(".", ","))

        self.slider.blockSignals(True)
        self.slider.setValue(int(round(metrics.static_offset_ms)))
        self.slider.blockSignals(False)

    def _on_slider_changed(self, value: int):
        self.current_offset = float(value)
        sign = "+" if self.current_offset >= 0 else "−"
        val_str = f"{abs(self.current_offset):.1f}".replace(".", ",")
        self.lbl_offset_val.setText(f"{sign}{val_str} ms")

        self.spin_offset.blockSignals(True)
        self.spin_offset.setValue(self.current_offset)
        self.spin_offset.blockSignals(False)

        self.offset_changed.emit(self.current_offset)

    def _on_spin_changed(self, value: float):
        self.current_offset = value
        sign = "+" if self.current_offset >= 0 else "−"
        val_str = f"{abs(self.current_offset):.1f}".replace(".", ",")
        self.lbl_offset_val.setText(f"{sign}{val_str} ms")

        self.slider.blockSignals(True)
        self.slider.setValue(int(round(value)))
        self.slider.blockSignals(False)

        self.offset_changed.emit(self.current_offset)

    def add_offset(self, delta_ms: float):
        new_val = self.current_offset + delta_ms
        new_val = max(-60000.0, min(60000.0, new_val))
        self.current_offset = new_val

        sign = "+" if self.current_offset >= 0 else "−"
        val_str = f"{abs(self.current_offset):.1f}".replace(".", ",")
        self.lbl_offset_val.setText(f"{sign}{val_str} ms")

        self.slider.blockSignals(True)
        self.slider.setValue(int(round(new_val)))
        self.slider.blockSignals(False)

        self.spin_offset.blockSignals(True)
        self.spin_offset.setValue(new_val)
        self.spin_offset.blockSignals(False)

        self.offset_changed.emit(self.current_offset)

    def reset_to_calculated(self):
        self.current_offset = self.algorithmic_offset
        sign = "+" if self.current_offset >= 0 else "−"
        val_str = f"{abs(self.current_offset):.1f}".replace(".", ",")
        self.lbl_offset_val.setText(f"{sign}{val_str} ms")

        self.slider.blockSignals(True)
        self.slider.setValue(int(round(self.algorithmic_offset)))
        self.slider.blockSignals(False)

        self.spin_offset.blockSignals(True)
        self.spin_offset.setValue(self.algorithmic_offset)
        self.spin_offset.blockSignals(False)

        self.offset_changed.emit(self.current_offset)

    def reset(self):
        self.algorithmic_offset = 0.0
        self.current_offset = 0.0
        self.lbl_offset_val.setText("+0,0 ms")
        self.lbl_drift_val.setText("1,000000x")
        self.lbl_confidence.setText("Não analisado")
        self.slider.blockSignals(True)
        self.slider.setValue(0)
        self.slider.blockSignals(False)
        self.spin_offset.blockSignals(True)
        self.spin_offset.setValue(0.0)
        self.spin_offset.blockSignals(False)
        self.offset_changed.emit(0.0)

    def set_offset(self, offset_ms: float, is_calculated: bool = False):
        """Sets the offset value, updates slider and displays, and emits offset_changed signal."""
        clamped = max(-60000.0, min(60000.0, offset_ms))
        self.current_offset = clamped
        if is_calculated:
            self.algorithmic_offset = clamped

        sign = "+" if self.current_offset >= 0 else "−"
        val_str = f"{abs(self.current_offset):.1f}".replace(".", ",")
        self.lbl_offset_val.setText(f"{sign}{val_str} ms")

        self.slider.blockSignals(True)
        self.slider.setValue(int(round(self.current_offset)))
        self.slider.blockSignals(False)

        self.spin_offset.blockSignals(True)
        self.spin_offset.setValue(self.current_offset)
        self.spin_offset.blockSignals(False)

        self.offset_changed.emit(self.current_offset)

    def set_manual_offset(self, offset_ms: float) -> None:
        """Explicitly sets the manual temporal alignment offset in milliseconds."""
        self.set_offset(offset_ms, is_calculated=False)

    def set_sensitivity_mode(self, mode: Literal["fine", "normal", "coarse"]) -> None:
        """Sets slider precision sensitivity mode and updates segmented control buttons."""
        if hasattr(self, "sensitivity_controller"):
            self.sensitivity_controller.set_mode(mode)
        for btn, m in [
            (getattr(self, "btn_sens_fine", None), "fine"),
            (getattr(self, "btn_sens_normal", None), "normal"),
            (getattr(self, "btn_sens_coarse", None), "coarse"),
        ]:
            if btn is not None:
                is_active = (m == mode)
                btn.setProperty("active", "true" if is_active else "false")
                btn.style().unpolish(btn)
                btn.style().polish(btn)


