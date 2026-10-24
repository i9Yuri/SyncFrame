"""High-precision QPainter widget for visualizing cross-correlation peaks and acoustic waveforms."""

from typing import List, Optional

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QWidget


class CorrelationView(QFrame):
    """
    Renders the cross-correlation energy curve and alignment peak using hardware-accelerated QPainter.
    Adheres strictly to the Precision Bench workbench design system:
    - Neutral grid lines and scale indicators
    - Crisp high-contrast signal trace
    - Main peak highlighted in Signal Accent (#d9f56b / #c1df50)
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumHeight(155)
        self.setObjectName("bentoCard")
        self.setProperty("class", "bentoCard")
        self.curve_points: List[float] = []
        self._curve_data: List[float] = []
        self.peak_offset_ms: float = 0.0
        self.confidence: float = 0.0
        self.status_text: str = "Aguardando execução da correlação espectral"
        self.is_light_mode: bool = False

    def set_theme_mode(self, mode: str):
        self.is_light_mode = (mode == "light")
        self.update()

    def set_data(self, points: List[float], offset_ms: float, confidence: float, status: str = ""):
        self.curve_points = points
        self._curve_data = points
        self.peak_offset_ms = offset_ms
        self.confidence = confidence
        self.status_text = status or (f"Pico de Correlação: {offset_ms:+.1f} ms (Confiança: {confidence * 100:.1f}%)")
        self.update()

    def set_status(self, text: str):
        self.status_text = text
        self.update()

    def clear(self):
        self.curve_points = []
        self.peak_offset_ms = 0.0
        self.confidence = 0.0
        self.status_text = "Aguardando execução da correlação espectral"
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        margin_x = 24
        margin_y = 28
        plot_w = w - (2 * margin_x)
        plot_h = h - (2 * margin_y)

        # Dynamic palette according to theme
        if self.is_light_mode:
            grid_color = QColor("#d1d1d1")
            center_color = QColor("#a8a8a8")
            curve_color = QColor("#111111")
            signal_color = QColor("#111111")
            signal_fill = QColor(0, 0, 0, 25)
            text_color = QColor("#4a4a4a")
            header_color = QColor("#111111")
        else:
            grid_color = QColor("#383838")
            center_color = QColor("#555555")
            curve_color = QColor("#ffffff")
            signal_color = QColor("#ffffff")
            signal_fill = QColor(255, 255, 255, 25)
            text_color = QColor("#a8a8a8")
            header_color = QColor("#ffffff")

        # Draw background grid lines (horizontal)
        grid_pen = QPen(grid_color)
        grid_pen.setWidth(1)
        grid_pen.setStyle(Qt.DotLine)
        painter.setPen(grid_pen)

        for frac in (0.25, 0.5, 0.75):
            y_pos = int(margin_y + frac * plot_h)
            painter.drawLine(margin_x, y_pos, w - margin_x, y_pos)

        # Vertical time scale division lines
        for frac in (0.166, 0.333, 0.5, 0.666, 0.833):
            x_pos = int(margin_x + frac * plot_w)
            painter.drawLine(x_pos, margin_y, x_pos, h - margin_y)

        # Central alignment line (0ms baseline)
        center_x = int(margin_x + (plot_w / 2.0))
        center_pen = QPen(center_color)
        center_pen.setWidth(1)
        painter.setPen(center_pen)
        painter.drawLine(center_x, margin_y, center_x, h - margin_y)

        if not self.curve_points or len(self.curve_points) < 2:
            # Render placeholder state
            painter.setPen(text_color)
            font = QFont("SFMono-Regular", 10)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, self.status_text)
            return

        # Normalize points to plot height
        max_val = max(self.curve_points) if self.curve_points else 1.0
        min_val = min(self.curve_points) if self.curve_points else 0.0
        val_range = max(1e-6, max_val - min_val)

        path = QPainterPath()
        n_points = len(self.curve_points)
        peak_idx = 0
        highest_y = h

        for i, val in enumerate(self.curve_points):
            norm_val = (val - min_val) / val_range
            x = margin_x + (i / float(n_points - 1)) * plot_w
            y = (margin_y + plot_h) - (norm_val * plot_h)

            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

            if y < highest_y:
                highest_y = y
                peak_idx = i

        # Fill under curve
        fill_path = QPainterPath(path)
        fill_path.lineTo(margin_x + plot_w, margin_y + plot_h)
        fill_path.lineTo(margin_x, margin_y + plot_h)
        fill_path.closeSubpath()
        painter.fillPath(fill_path, signal_fill)

        # Draw energy curve
        curve_pen = QPen(curve_color)
        curve_pen.setWidth(2)
        painter.setPen(curve_pen)
        painter.drawPath(path)

        # Highlight peak with signal accent line
        peak_x = margin_x + (peak_idx / float(n_points - 1)) * plot_w
        peak_pen = QPen(signal_color)
        peak_pen.setWidth(2)
        peak_pen.setStyle(Qt.DashLine)
        painter.setPen(peak_pen)
        painter.drawLine(int(peak_x), margin_y, int(peak_x), h - margin_y)

        # Peak indicator dot
        painter.setBrush(signal_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(peak_x, highest_y), 4.5, 4.5)

        # Telemetry Header Text
        painter.setPen(header_color)
        font = QFont("SFMono-Regular", 10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(margin_x, margin_y - 10, self.status_text)
