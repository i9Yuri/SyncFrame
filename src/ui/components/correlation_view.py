"""High-precision QPainter widget for visualizing cross-correlation peaks and acoustic waveforms."""

from typing import List, Optional

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QWidget


class CorrelationView(QFrame):
    """
    Renders the cross-correlation energy curve and alignment peak using hardware-accelerated QPainter.
    Adheres to the Pro Max v4 Anti-Slop color scheme (Dark Slate, Cyan, Emerald).
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumHeight(140)
        self.setObjectName("bentoCard")
        self.setProperty("class", "bentoCard")
        self.curve_points: List[float] = []
        self.peak_offset_ms: float = 0.0
        self.confidence: float = 0.0
        self.status_text: str = "Aguardando execução da correlação espectral"

    def set_data(self, points: List[float], offset_ms: float, confidence: float, status: str = ""):
        self.curve_points = points
        self.peak_offset_ms = offset_ms
        self.confidence = confidence
        self.status_text = status or (f"Pico de Correlação: {offset_ms:+.1f} ms (Confiança: {confidence * 100:.1f}%)")
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
        margin_x = 20
        margin_y = 25
        plot_w = w - (2 * margin_x)
        plot_h = h - (2 * margin_y)

        # Draw background grid lines
        grid_pen = QPen(QColor("#1e293b"))
        grid_pen.setWidth(1)
        grid_pen.setStyle(Qt.DashLine)
        painter.setPen(grid_pen)

        # 3 horizontal grid lines
        for frac in (0.25, 0.5, 0.75):
            y_pos = int(margin_y + frac * plot_h)
            painter.drawLine(margin_x, y_pos, w - margin_x, y_pos)

        # Central alignment line
        center_x = int(margin_x + (plot_w / 2.0))
        center_pen = QPen(QColor("#334155"))
        center_pen.setWidth(1)
        painter.setPen(center_pen)
        painter.drawLine(center_x, margin_y, center_x, h - margin_y)

        if not self.curve_points or len(self.curve_points) < 2:
            # Render placeholder text
            painter.setPen(QColor("#64748b"))
            font = QFont("Inter", 11)
            painter.setFont(font)
            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                self.status_text
            )
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

        # Draw energy curve in surgical cyan
        curve_pen = QPen(QColor("#06b6d4"))
        curve_pen.setWidth(2)
        painter.setPen(curve_pen)
        painter.drawPath(path)

        # Highlight peak with emerald/cyan marker
        peak_x = margin_x + (peak_idx / float(n_points - 1)) * plot_w
        peak_pen = QPen(QColor("#10b981") if self.confidence >= 0.35 else QColor("#f59e0b"))
        peak_pen.setWidth(2)
        painter.setPen(peak_pen)
        painter.drawLine(int(peak_x), margin_y, int(peak_x), h - margin_y)

        # Draw circle on peak
        painter.setBrush(QColor("#10b981") if self.confidence >= 0.35 else QColor("#f59e0b"))
        painter.drawEllipse(QPointF(peak_x, highest_y), 4.5, 4.5)

        # Render status banner at top
        painter.setPen(QColor("#38bdf8"))
        font = QFont("JetBrains Mono", 10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(margin_x, margin_y - 8, self.status_text)
