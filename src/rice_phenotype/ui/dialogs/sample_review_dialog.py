# -*- coding: utf-8 -*-

"""
样本复核弹窗

用于查看批量分析中选中样本的原图、分割掩膜、叠加结果、指标和解释提示。
本弹窗仅用于结果复核，不提供农学诊断结论。
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


class SampleReviewDialog(QDialog):
    def __init__(
        self,
        sample_index: int,
        result,
        cm_per_pixel: float | None = None,
        parent=None,
    ):
        super().__init__(parent)

        self.sample_index = sample_index
        self.result = result
        self.cm_per_pixel = cm_per_pixel

        self.setWindowTitle("样本结果复核")
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

        title = QLabel(f"样本复核：第 {self.sample_index} 号 - {self.result.sample_name}")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #111827;")
        layout.addWidget(title)

        status = "成功" if self.result.success else "失败"
        status_label = QLabel(
            f"分析状态：{status}\n"
            f"提示信息：{self.result.message}\n"
            f"原始图像路径：{self.result.image_path}"
        )
        status_label.setWordWrap(True)
        status_label.setStyleSheet("font-size: 13px; color: #374151; line-height: 1.6;")
        layout.addWidget(self._wrap_card(status_label))

        image_layout = QHBoxLayout()
        image_layout.setSpacing(14)

        original_image = self._read_original_image()
        mask_image = getattr(self.result, "mask", None)
        overlay_image = getattr(self.result, "overlay", None)

        self.original_panel = self._create_image_panel("原始图像", original_image)
        self.mask_panel = self._create_image_panel("分割掩膜", mask_image)
        self.overlay_panel = self._create_image_panel("叠加结果", overlay_image)

        image_layout.addWidget(self.original_panel)
        image_layout.addWidget(self.mask_panel)
        image_layout.addWidget(self.overlay_panel)

        layout.addLayout(image_layout)

        metrics_label = QLabel(self._format_metrics_text())
        metrics_label.setWordWrap(True)
        metrics_label.setStyleSheet("font-size: 13px; color: #374151; line-height: 1.7;")
        layout.addWidget(self._wrap_card(metrics_label, title="表型指标"))

        insight_label = QLabel(self._format_insight_text())
        insight_label.setWordWrap(True)
        insight_label.setStyleSheet("font-size: 13px; color: #374151; line-height: 1.7;")
        layout.addWidget(self._wrap_card(insight_label, title="复核提示"))

        note = QLabel(
            "说明：本弹窗用于复核批量分析中单个样本的图像、掩膜、叠加图和指标结果。"
            "复核提示基于二维图像指标和软件内部评分生成，仅用于辅助查看，不作为农学诊断、病害判断或生产决策依据。"
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
            title_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #111827;")
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
            image_label.setText("暂无图像")
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

    def _read_original_image(self) -> np.ndarray | None:
        path = Path(self.result.image_path)

        if not path.exists():
            return None

        image_bgr = cv2.imdecode(
            np.fromfile(str(path), dtype=np.uint8),
            cv2.IMREAD_COLOR,
        )

        if image_bgr is None:
            return None

        return cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    def _format_metrics_text(self) -> str:
        metrics = getattr(self.result, "metrics", None)

        if not self.result.success or metrics is None:
            return "当前样本未获得有效指标结果，可查看分析状态和失败原因。"

        scale_text = "-"
        if self.cm_per_pixel is not None:
            scale_text = f"{float(self.cm_per_pixel):.5f} cm/pixel"

        return (
            f"比例尺：{scale_text}\n"
            f"图像尺寸：{self.result.image_width} × {self.result.image_height} px\n"
            f"株高估算：{metrics.plant_height_cm:.2f} cm ({metrics.plant_height_px:.0f} px)\n"
            f"冠幅估算：{metrics.canopy_width_cm:.2f} cm ({metrics.canopy_width_px:.0f} px)\n"
            f"投影面积：{metrics.projected_area_cm2:.2f} cm² ({metrics.projected_area_px:.0f} px)\n"
            f"绿色覆盖率：{metrics.green_coverage * 100:.2f}%\n"
            f"ExG 叶色指数均值：{metrics.exg_mean:.2f}\n"
            f"Green Ratio：{metrics.green_ratio:.4f}\n"
            f"外接矩形填充率：{metrics.bbox_fill_ratio * 100:.2f}%\n"
            f"长势评分：{metrics.growth_score:.2f} / 100"
        )

    def _format_insight_text(self) -> str:
        metrics = getattr(self.result, "metrics", None)

        if not self.result.success or metrics is None:
            return (
                "当前样本未得到有效分析结果。建议检查图像是否可读取、拍摄背景是否过于复杂、"
                "秧苗区域是否清晰，以及分割参数是否适合当前图像。"
            )

        score = float(metrics.growth_score)
        coverage = float(metrics.green_coverage)
        fill_ratio = float(metrics.bbox_fill_ratio)

        lines = [
            f"当前样本长势评分为 {score:.2f}，该评分为软件内部综合评分，适合用于同批次样本之间的相对比较。"
        ]

        if score >= 80:
            lines.append("该样本处于内部评分较高区间，可结合原图、掩膜图和叠加图确认分割结果是否符合预期。")
        elif score >= 60:
            lines.append("该样本处于内部评分中等区间，建议结合本批次其他样本进行对照查看。")
        else:
            lines.append("该样本处于内部评分偏低区间，建议优先复核图像质量、分割效果、比例尺设置和实际样本状态。")

        lines.append(
            f"绿色覆盖率为 {coverage * 100:.2f}%，可结合叠加图查看绿色区域提取是否覆盖主要秧苗区域。"
        )

        if coverage < 0.15:
            lines.append("绿色覆盖率相对较低，可能与图像背景占比、秧苗区域占比、光照条件或阈值参数有关。")
        elif coverage > 0.70:
            lines.append("绿色覆盖率相对较高，建议确认掩膜是否覆盖了非秧苗绿色区域。")

        if fill_ratio < 0.20:
            lines.append("外接矩形填充率较低，可能说明掩膜区域较分散，建议检查是否存在背景干扰或分割碎片。")

        lines.append("以上提示仅用于辅助复核，不作为农学诊断、病害判断、品种评价或生产决策依据。")

        return "\n".join(lines)

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

        raise ValueError("不支持的图像数组格式。")