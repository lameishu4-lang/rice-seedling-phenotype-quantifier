# -*- coding: utf-8 -*-

"""
轻量级图表控件

本模块使用 PySide6 QPainter 自绘简单图表，不依赖额外第三方可视化库。
用于批量分析结果的直观展示。

设计原则：
1. 图表控件内部只负责绘制图形，不绘制长说明文字；
2. 柱状图横轴使用样本序号，对应下方明细表中的序号；
3. 长文件名不直接显示在横轴上，避免标签重叠；
4. 图表仅用于样本间相对比较，不作为农学诊断结论。
"""

from math import ceil

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PySide6.QtWidgets import QWidget


class BarChartWidget(QWidget):
    """简单柱状图控件"""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)

        self.title = title
        self.labels: list[str] = []
        self.values: list[float] = []
        self.unit = ""
        self.max_items = 30

        self.setMinimumHeight(230)

    def set_data(
        self,
        title: str,
        labels: list[str],
        values: list[float],
        unit: str = "",
        max_items: int = 30,
    ) -> None:
        self.title = title
        self.labels = labels[:max_items]
        self.values = values[:max_items]
        self.unit = unit
        self.max_items = max_items
        self.update()

    def clear(self) -> None:
        self.labels = []
        self.values = []
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(12, 10, -12, -12)

        self._draw_title(painter, rect)

        chart_rect = QRectF(
            rect.left() + 8,
            rect.top() + 42,
            rect.width() - 16,
            rect.height() - 54,
        )

        if not self.values:
            painter.setPen(QPen(QColor("#6B7280")))
            painter.drawText(chart_rect, Qt.AlignCenter, "暂无可视化数据")
            return

        self._draw_bars(painter, chart_rect)
        self._draw_stats_text(painter, chart_rect)
        self._draw_axis_labels(painter, chart_rect)

    def _draw_title(self, painter: QPainter, rect) -> None:
        painter.setPen(QPen(QColor("#111827")))

        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        painter.setFont(title_font)

        painter.drawText(
            int(rect.left()),
            int(rect.top()),
            int(rect.width()),
            24,
            Qt.AlignLeft,
            self.title,
        )

    def _draw_bars(self, painter: QPainter, chart_rect: QRectF) -> None:
        max_value = max(self.values)

        if max_value <= 0:
            max_value = 1.0

        painter.setPen(QPen(QColor("#CBD5E1")))

        baseline_y = chart_rect.bottom()
        painter.drawLine(
            int(chart_rect.left()),
            int(baseline_y),
            int(chart_rect.right()),
            int(baseline_y),
        )

        count = len(self.values)
        slot_width = chart_rect.width() / max(count, 1)
        bar_width = max(4, min(24, slot_width * 0.62))

        bar_color = QColor("#2563EB")

        for index, value in enumerate(self.values):
            bar_height = chart_rect.height() * float(value) / max_value
            x = chart_rect.left() + index * slot_width + (slot_width - bar_width) / 2
            y = chart_rect.bottom() - bar_height

            bar_rect = QRectF(x, y, bar_width, bar_height)

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(bar_color))
            painter.drawRoundedRect(bar_rect, 3, 3)

    def _draw_stats_text(self, painter: QPainter, chart_rect: QRectF) -> None:
        if not self.values:
            return

        painter.setPen(QPen(QColor("#374151")))

        small_font = QFont()
        small_font.setPointSize(8)
        painter.setFont(small_font)

        mean_value = sum(self.values) / len(self.values)
        max_value = max(self.values)

        stats_text = (
            f"均值：{mean_value:.2f}{self.unit}；"
            f"最大值：{max_value:.2f}{self.unit}"
        )

        if len(self.labels) >= self.max_items:
            stats_text += f"；显示前 {self.max_items} 项"

        painter.drawText(
            int(chart_rect.left()),
            int(chart_rect.top() - 22),
            int(chart_rect.width()),
            18,
            Qt.AlignRight,
            stats_text,
        )

    def _draw_axis_labels(self, painter: QPainter, chart_rect: QRectF) -> None:
        count = len(self.values)

        if count == 0:
            return

        painter.setPen(QPen(QColor("#6B7280")))

        label_font = QFont()
        label_font.setPointSize(8)
        painter.setFont(label_font)

        slot_width = chart_rect.width() / max(count, 1)
        visible_indices = self._visible_label_indices(count)

        for index in visible_indices:
            x = chart_rect.left() + index * slot_width

            label_rect = QRectF(
                x,
                chart_rect.bottom() + 5,
                max(slot_width, 22),
                18,
            )

            painter.drawText(
                label_rect,
                Qt.AlignLeft | Qt.AlignVCenter,
                str(index + 1),
            )

    @staticmethod
    def _visible_label_indices(count: int) -> list[int]:
        if count <= 12:
            return list(range(count))

        step = max(1, ceil(count / 8))
        indices = list(range(0, count, step))

        if count - 1 not in indices:
            indices.append(count - 1)

        return indices


class ScoreLevelWidget(QWidget):
    """长势评分等级统计条"""

    def __init__(self, title: str = "评分等级统计", parent=None):
        super().__init__(parent)

        self.title = title
        self.scores: list[float] = []

        self.setMinimumHeight(230)

    def set_scores(self, scores: list[float]) -> None:
        self.scores = scores
        self.update()

    def clear(self) -> None:
        self.scores = []
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(12, 10, -12, -12)

        self._draw_title(painter, rect)

        content_rect = QRectF(
            rect.left() + 8,
            rect.top() + 42,
            rect.width() - 16,
            rect.height() - 46,
        )

        if not self.scores:
            painter.setPen(QPen(QColor("#6B7280")))
            painter.drawText(content_rect, Qt.AlignCenter, "暂无评分数据")
            return

        excellent = sum(1 for score in self.scores if score >= 80)
        good = sum(1 for score in self.scores if 60 <= score < 80)
        weak = sum(1 for score in self.scores if score < 60)
        total = len(self.scores)

        self._draw_summary_text(
            painter=painter,
            content_rect=content_rect,
            total=total,
            excellent=excellent,
            good=good,
            weak=weak,
        )

        self._draw_level_bar(
            painter=painter,
            content_rect=content_rect,
            total=total,
            excellent=excellent,
            good=good,
            weak=weak,
        )

        self._draw_legend(
            painter=painter,
            content_rect=content_rect,
            total=total,
            excellent=excellent,
            good=good,
            weak=weak,
        )

    def _draw_title(self, painter: QPainter, rect) -> None:
        painter.setPen(QPen(QColor("#111827")))

        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        painter.setFont(title_font)

        painter.drawText(
            int(rect.left()),
            int(rect.top()),
            int(rect.width()),
            24,
            Qt.AlignLeft,
            self.title,
        )

    @staticmethod
    def _draw_summary_text(
        painter: QPainter,
        content_rect: QRectF,
        total: int,
        excellent: int,
        good: int,
        weak: int,
    ) -> None:
        summary_text = (
            f"总数：{total}；"
            f"高评分(≥80)：{excellent}；"
            f"中等(60–80)：{good}；"
            f"偏低(<60)：{weak}"
        )

        painter.setPen(QPen(QColor("#374151")))

        small_font = QFont()
        small_font.setPointSize(9)
        painter.setFont(small_font)

        painter.drawText(
            int(content_rect.left()),
            int(content_rect.top()),
            int(content_rect.width()),
            24,
            Qt.AlignLeft,
            summary_text,
        )

    @staticmethod
    def _draw_level_bar(
        painter: QPainter,
        content_rect: QRectF,
        total: int,
        excellent: int,
        good: int,
        weak: int,
    ) -> None:
        bar_rect = QRectF(
            content_rect.left(),
            content_rect.top() + 46,
            content_rect.width(),
            28,
        )

        painter.setPen(Qt.NoPen)

        segments = [
            ("高评分", excellent, QColor("#16A34A")),
            ("中等", good, QColor("#2563EB")),
            ("偏低", weak, QColor("#F97316")),
        ]

        current_x = bar_rect.left()

        for _, count, color in segments:
            if count <= 0:
                continue

            width = bar_rect.width() * count / total
            segment_rect = QRectF(current_x, bar_rect.top(), width, bar_rect.height())

            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(segment_rect, 5, 5)

            current_x += width

    @staticmethod
    def _draw_legend(
        painter: QPainter,
        content_rect: QRectF,
        total: int,
        excellent: int,
        good: int,
        weak: int,
    ) -> None:
        segments = [
            ("高评分", excellent, QColor("#16A34A")),
            ("中等", good, QColor("#2563EB")),
            ("偏低", weak, QColor("#F97316")),
        ]

        legend_y = content_rect.top() + 92
        legend_x = content_rect.left()

        small_font = QFont()
        small_font.setPointSize(8)
        painter.setFont(small_font)

        for name, count, color in segments:
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(legend_x, legend_y, 12, 12), 2, 2)

            painter.setPen(QPen(QColor("#374151")))

            percent = count / total * 100 if total else 0
            text = f"{name}: {count} ({percent:.1f}%)"

            painter.drawText(
                int(legend_x + 18),
                int(legend_y - 2),
                150,
                18,
                Qt.AlignLeft,
                text,
            )

            legend_y += 24