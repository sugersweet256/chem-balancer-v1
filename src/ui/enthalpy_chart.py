"""Qt 原生反应焓变图。

作为 matplotlib 不可用时的后备实现；只读取 substances_energy 数据，不修改
核心代码。画风与配平器一致，不依赖额外的绘图库。
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget


class EnthalpyChart(QWidget):
    def __init__(
        self,
        delta_h: float,
        equation: str = "",
        activation_energy: float = 80.0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.delta_h = delta_h
        self.equation = equation
        self.activation_energy = activation_energy
        self.setMinimumHeight(250)
        self.setStyleSheet("background: #FFFFFF;")

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#FFFFFF"))

        width = self.width()
        height = self.height()
        title_rect = QRectF(8, 3, width - 16, 20)
        if self.equation:
            painter.setPen(QColor("#33495E"))
            painter.setFont(QFont("Microsoft YaHei UI", 9))
            painter.drawText(title_rect, Qt.AlignHCenter | Qt.AlignVCenter, self.equation)

        plot = QRectF(58, 30, max(20, width - 86), max(20, height - 68))
        if plot.width() <= 10 or plot.height() <= 10:
            return

        delta = self.delta_h
        span = max(abs(delta), 100.0)
        y_reactant = 0.0
        y_product = delta / span
        y_peak = max(y_reactant, y_product) + max(self.activation_energy / span, 0.18)
        y_low = min(y_reactant, y_product) - 0.18
        y_high = y_peak + 0.30

        def px(value: float) -> float:
            return plot.left() + (value / 10.0) * plot.width()

        def py(value: float) -> float:
            ratio = (value - y_low) / max(y_high - y_low, 1e-9)
            return plot.bottom() - ratio * plot.height()

        points = [
            QPointF(px(0), py(y_reactant)),
            QPointF(px(3), py(y_reactant)),
            QPointF(px(5), py(y_peak)),
            QPointF(px(7), py(y_product)),
            QPointF(px(10), py(y_product)),
        ]

        polygon = QPolygonF(
            [points[0], points[1], points[2], points[3], points[4],
             QPointF(px(10), plot.bottom()), QPointF(px(0), plot.bottom())]
        )
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(166, 206, 227, 75)))
        painter.drawPolygon(polygon)

        painter.setPen(QPen(QColor("#2166AC"), 2.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawPolyline(QPolygonF(points))

        self._draw_arrow(
            painter,
            px(1.6),
            py(y_reactant),
            py(y_product),
            QColor("#33495E"),
            dashed=False,
        )
        painter.setPen(QColor("#33495E"))
        painter.setFont(QFont("Microsoft YaHei UI", 8))
        painter.drawText(
            QRectF(px(1.6) + 7, (py(y_reactant) + py(y_product)) / 2 - 10, 120, 20),
            Qt.AlignLeft | Qt.AlignVCenter,
            f"ΔH = {delta:.0f} kJ/mol",
        )

        self._draw_arrow(
            painter,
            px(2.9),
            py(y_reactant),
            py(y_peak),
            QColor("#667788"),
            dashed=True,
        )
        painter.setPen(QColor("#667788"))
        painter.setFont(QFont("Microsoft YaHei UI", 7))
        painter.drawText(
            QRectF(px(2.9) + 6, (py(y_reactant) + py(y_peak)) / 2 - 9, 130, 18),
            Qt.AlignLeft | Qt.AlignVCenter,
            f"Ea ≈ {self.activation_energy:.0f} kJ/mol",
        )

        painter.setFont(QFont("Microsoft YaHei UI", 8))
        painter.setPen(QColor("#2166AC"))
        painter.drawText(
            QRectF(px(0) - 4, py(y_reactant) - 24, 80, 18),
            Qt.AlignLeft | Qt.AlignVCenter,
            "反应物",
        )
        painter.setPen(QColor("#B2182B"))
        painter.drawText(
            QRectF(px(9) - 50, py(y_product) - 24, 80, 18),
            Qt.AlignRight | Qt.AlignVCenter,
            "生成物",
        )
        painter.setPen(QColor("#445566"))
        painter.drawText(
            QRectF(px(5) - 45, py(y_peak) - 24, 90, 18),
            Qt.AlignCenter,
            "过渡态",
        )

        kind = "放热反应" if delta < 0 else ("吸热反应" if delta > 0 else "能量不变")
        painter.setPen(QColor("#7A8A99"))
        painter.setFont(QFont("Microsoft YaHei UI", 8))
        painter.drawText(
            QRectF(plot.right() - 100, plot.top() - 1, 100, 18),
            Qt.AlignRight | Qt.AlignVCenter,
            kind,
        )

        painter.setPen(QColor("#8493A1"))
        painter.setFont(QFont("Microsoft YaHei UI", 8))
        painter.drawText(
            QRectF(plot.left(), plot.bottom() + 10, plot.width(), 18),
            Qt.AlignHCenter | Qt.AlignTop,
            "反应进程",
        )
        painter.save()
        painter.translate(15, plot.center().y())
        painter.rotate(-90)
        painter.drawText(
            QRectF(-plot.height() / 2, -10, plot.height(), 18),
            Qt.AlignCenter,
            "能量",
        )
        painter.restore()

    @staticmethod
    def _draw_arrow(
        painter: QPainter,
        x: float,
        y1: float,
        y2: float,
        color: QColor,
        dashed: bool,
    ) -> None:
        pen = QPen(color, 1.2)
        pen.setStyle(Qt.DashLine if dashed else Qt.SolidLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(x, y1), QPointF(x, y2))
        head = 5.0
        down = 1.0 if y2 > y1 else -1.0
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawPolygon(
            QPolygonF(
                [
                    QPointF(x, y1 - 7 * down),
                    QPointF(x - head, y1),
                    QPointF(x + head, y1),
                ]
            )
        )
        painter.drawPolygon(
            QPolygonF(
                [
                    QPointF(x, y2 + 7 * down),
                    QPointF(x - head, y2),
                    QPointF(x + head, y2),
                ]
            )
        )
        painter.setBrush(Qt.NoBrush)
