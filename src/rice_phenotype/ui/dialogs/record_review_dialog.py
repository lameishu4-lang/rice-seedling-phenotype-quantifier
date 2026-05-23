# -*- coding: utf-8 -*-

"""
历史记录详情复核弹窗

用于查看历史记录中的原始图像、分割掩膜、叠加结果、指标、备注和解释提示。
本弹窗仅用于记录回看和结果复核，不提供农学诊断结论。
"""

from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QScrollArea,
    QWidget,
)


class RecordReviewDialog(QDialog):
    def __init__(
        self,
        display_index: int,
        record: dict,
        parent=None,
    ):
        super().__init__(parent)

        self.display_index = display_index
        self.record = record

        self.setWindowTitle("历史记录详情")
        self.resize(1180, 780)

        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(16)

        scroll_area.setWidget(content)
        root_layout.addWidget(scroll_area)

        title = QLabel(
            f"历史记录详情：第 {self.display_index} 条 - "
            f"{self.record.get('sample_name', '')}"
        )
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #111827;")
        layout.addWidget(title)

        basic_label = QLabel(self._format_basic_text())
        basic_label.setWordWrap(True)
        basic_label.setStyleSheet("font-size: 13px; color: #374151; line-height: 1.7;")
        layout.addWidget(self._wrap_card(basic_label, title="记录信息"))

        image_layout = QHBoxLayout()
        image_layout.setSpacing(14)

        original_image = self._read_image(
            self.record.get("image_path", ""),
            force_rgb=True,
        )
        mask_image = self._read_image(
            self.record.get("mask_path", ""),
            force_rgb=False,
        )
        overlay_image = self._read_image(
            self.record.get("overlay_path", ""),
            force_rgb=True,
        )

        image_layout.addWidget(self._create_image_panel("原始图像", original_image))
        image_layout.addWidget(self._create_image_panel("分割掩膜", mask_image))
        image_layout.addWidget(self._create_image_panel("叠加结果", overlay_image))

        layout.addLayout(image_layout)

        metrics_label = QLabel(self._format_metrics_text())
        metrics_label.setWordWrap(True)
        metrics_label.setStyleSheet("font-size: 13px; color: #374151; line-height: 1.7;")
        layout.addWidget(self._wrap_card(metrics_label, title="表型指标"))

        insight_label = QLabel(self._format_insight_text())
        insight_label.setWordWrap(True)
        insight_label.setStyleSheet("font-size: 13px; color: #374151; line-height: 1.7;")
        layout.addWidget(self._wrap_card(insight_label, title="记录复核提示"))

        note = QLabel(
            "说明：本弹窗用于查看已保存历史记录的图像、指标和备注信息。"
            "复核提示基于二维图像指标和软件内部评分生成，仅用于辅助查看，"
            "不作为农学诊断、病害判断、品种评价或生产决策依据。"
        )
        note.setWordWrap(True)
        note.setStyleSheet("font-size: 12px; color: #6B7280;")
        layout.addWidget(note)

        close_layout = QHBoxLayout()
        close_layout.addStretch()

        btn_close = QPushButton("关闭")
        btn_close.setFixedWidth(100)
        btn_close.clicked.connect(self.accept)

        close_layout.addWidget(btn_close)
        layout.addLayout(close_layout)

    def _wrap_card(self, widget: QWidget, title: str | None = None) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(
            """
            QFrame#Card {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(
                "font-size: 16px; font-weight: 700; color: #111827;"
            )
            layout.addWidget(title_label)

        layout.addWidget(widget)

        return card

    def _create_image_panel(self, title: str, image: np.ndarray | None) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(
            """
            QFrame#Card {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #111827;")
        layout.addWidget(title_label)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumHeight(300)
        image_label.setStyleSheet(
            """
            QLabel {
                background-color: #F9FAFB;
                border: 1px dashed #CBD5E1;
                border-radius: 10px;
                color: #6B7280;
            }
            """
        )

        if image is None:
            image_label.setText("暂无图像或文件路径失效")
        else:
            pixmap = self._ndarray_to_pixmap(image)
            image_label.setPixmap(
                pixmap.scaled(
                    330,
                    300,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )

        layout.addWidget(image_label)

        return card

    def _format_basic_text(self) -> str:
        return (
            f"显示序号：{self.display_index}\n"
            f"内部记录ID：{self.record.get('id', '')}\n"
            f"样本名称：{self.record.get('sample_name', '')}\n"
            f"分析时间：{self.record.get('analysis_time', '')}\n"
            f"软件版本：{self.record.get('software_version', '')}\n"
            f"原始图像路径：{self.record.get('image_path', '')}\n"
            f"掩膜图路径：{self.record.get('mask_path', '')}\n"
            f"叠加图路径：{self.record.get('overlay_path', '')}\n"
            f"备注：{self.record.get('note', '') or '无'}"
        )

    def _format_metrics_text(self) -> str:
        return (
            f"比例尺：{self._format_float(self.record.get('cm_per_pixel'), 5)} cm/pixel\n"
            f"图像尺寸：{self.record.get('image_width', '')} × "
            f"{self.record.get('image_height', '')} px\n"
            f"分割方法：{self.record.get('segmentation_method', '')}\n"
            f"HSV 下限：{self.record.get('hsv_lower', '')}\n"
            f"HSV 上限：{self.record.get('hsv_upper', '')}\n"
            f"ExG 阈值：{self.record.get('exg_threshold', '')}\n\n"
            f"株高估算：{self._format_float(self.record.get('plant_height_cm'), 2)} cm "
            f"({self._format_float(self.record.get('plant_height_px'), 0)} px)\n"
            f"冠幅估算：{self._format_float(self.record.get('canopy_width_cm'), 2)} cm "
            f"({self._format_float(self.record.get('canopy_width_px'), 0)} px)\n"
            f"投影面积：{self._format_float(self.record.get('projected_area_cm2'), 2)} cm² "
            f"({self._format_float(self.record.get('projected_area_px'), 0)} px)\n"
            f"绿色覆盖率：{self._format_percent(self.record.get('green_coverage'))}\n"
            f"ExG 叶色指数均值：{self._format_float(self.record.get('exg_mean'), 2)}\n"
            f"Green Ratio：{self._format_float(self.record.get('green_ratio'), 4)}\n"
            f"外接矩形填充率：{self._format_percent(self.record.get('bbox_fill_ratio'))}\n"
            f"长势评分：{self._format_float(self.record.get('growth_score'), 2)} / 100"
        )

    def _format_insight_text(self) -> str:
        score = self._to_float(self.record.get("growth_score"))
        coverage = self._to_float(self.record.get("green_coverage"))
        fill_ratio = self._to_float(self.record.get("bbox_fill_ratio"))
        cm_per_pixel = self._to_float(self.record.get("cm_per_pixel"))

        if score is None:
            return "当前记录缺少有效评分信息，建议查看原图、掩膜图和叠加图进行人工复核。"

        lines: list[str] = [
            f"当前记录的长势评分为 {score:.2f}，该评分为软件内部综合评分，适合用于同批次样本之间的相对比较。"
        ]

        if score >= 80:
            lines.append(
                "该记录处于内部评分较高区间，可结合原图、掩膜图和叠加图确认分割结果是否符合预期。"
            )
        elif score >= 60:
            lines.append(
                "该记录处于内部评分中等区间，建议结合相同批次或相同拍摄条件下的其他记录进行对照查看。"
            )
        else:
            lines.append(
                "该记录处于内部评分偏低区间，建议优先复核图像质量、分割效果、比例尺设置和实际样本状态。"
            )

        if coverage is not None:
            lines.append(
                f"绿色覆盖率为 {coverage * 100:.2f}%，可结合叠加图查看绿色区域提取是否覆盖主要秧苗区域。"
            )

            if coverage < 0.15:
                lines.append(
                    "绿色覆盖率相对较低，可能与图像背景占比、秧苗区域占比、光照条件或阈值参数有关。"
                )
            elif coverage > 0.70:
                lines.append(
                    "绿色覆盖率相对较高，建议确认掩膜是否覆盖了非秧苗绿色区域。"
                )

        if fill_ratio is not None and fill_ratio < 0.20:
            lines.append(
                "外接矩形填充率较低，可能说明掩膜区域较分散，建议检查是否存在背景干扰、遮挡或分割碎片。"
            )

        if cm_per_pixel is not None:
            lines.append(
                f"该记录保存时使用的比例尺为 {cm_per_pixel:.5f} cm/pixel，株高、冠幅和投影面积均依赖该比例尺。"
            )

        lines.append(
            "以上提示仅用于辅助复核，不作为农学诊断、病害判断、品种评价或生产决策依据。"
        )

        return "\n".join(lines)

    @staticmethod
    def _read_image(path_text: str, force_rgb: bool) -> np.ndarray | None:
        if not path_text:
            return None

        path = Path(path_text)

        if not path.exists():
            return None

        flag = cv2.IMREAD_COLOR if force_rgb else cv2.IMREAD_UNCHANGED

        image = cv2.imdecode(
            np.fromfile(str(path), dtype=np.uint8),
            flag,
        )

        if image is None:
            return None

        if image.ndim == 2:
            return image

        if image.ndim == 3 and image.shape[2] == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        if image.ndim == 3 and image.shape[2] == 4:
            return cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)

        return None

    @staticmethod
    def _ndarray_to_pixmap(image: np.ndarray) -> QPixmap:
        if image.ndim == 2:
            height, width = image.shape
            bytes_per_line = width
            qimage = QImage(
                image.data,
                width,
                height,
                bytes_per_line,
                QImage.Format_Grayscale8,
            ).copy()
            return QPixmap.fromImage(qimage)

        if image.ndim == 3 and image.shape[2] == 3:
            height, width, _ = image.shape
            bytes_per_line = 3 * width
            qimage = QImage(
                image.data,
                width,
                height,
                bytes_per_line,
                QImage.Format_RGB888,
            ).copy()
            return QPixmap.fromImage(qimage)

        if image.ndim == 3 and image.shape[2] == 4:
            height, width, _ = image.shape
            bytes_per_line = 4 * width
            qimage = QImage(
                image.data,
                width,
                height,
                bytes_per_line,
                QImage.Format_RGBA8888,
            ).copy()
            return QPixmap.fromImage(qimage)

        raise ValueError("不支持的图像数组格式。")

    @staticmethod
    def _to_float(value) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _format_float(value, digits: int) -> str:
        if value is None:
            return "-"

        try:
            return f"{float(value):.{digits}f}"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _format_percent(value) -> str:
        if value is None:
            return "-"

        try:
            return f"{float(value) * 100:.2f}%"
        except (TypeError, ValueError):
            return str(value)