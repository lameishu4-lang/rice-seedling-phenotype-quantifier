# -*- coding: utf-8 -*-

from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QFrame,
    QMessageBox,
)

from rice_phenotype.core.segmentation import (
    SeedlingSegmenter,
    SegmentationConfig,
    SegmentationResult,
)
from rice_phenotype.utils.image_qt import ndarray_to_pixmap


class SingleAnalysisPage(QWidget):
    def __init__(self):
        super().__init__()

        self.current_image_path: Path | None = None
        self.current_image_rgb: np.ndarray | None = None
        self.current_segmentation: SegmentationResult | None = None

        self.segmenter = SeedlingSegmenter()

        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(36, 32, 36, 32)
        root_layout.setSpacing(18)

        title = QLabel("单张图像分析")
        title.setObjectName("PageTitle")
        root_layout.addWidget(title)

        desc = QLabel(
            "导入水稻秧苗图像，完成绿色植株区域分割、掩膜预览和后续表型指标计算。"
        )
        desc.setObjectName("PageDesc")
        desc.setWordWrap(True)
        root_layout.addWidget(desc)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.btn_import = QPushButton("导入图像")
        self.btn_import.setObjectName("PrimaryButton")
        self.btn_import.clicked.connect(self.import_image)

        self.btn_segment = QPushButton("执行分割")
        self.btn_segment.setObjectName("SecondaryButton")
        self.btn_segment.setEnabled(False)
        self.btn_segment.clicked.connect(self.run_segmentation)

        self.btn_calculate = QPushButton("计算指标")
        self.btn_calculate.setObjectName("SecondaryButton")
        self.btn_calculate.setEnabled(False)

        self.btn_save = QPushButton("保存记录")
        self.btn_save.setObjectName("SecondaryButton")
        self.btn_save.setEnabled(False)

        self.btn_report = QPushButton("导出报告")
        self.btn_report.setObjectName("SecondaryButton")
        self.btn_report.setEnabled(False)

        toolbar.addWidget(self.btn_import)
        toolbar.addWidget(self.btn_segment)
        toolbar.addWidget(self.btn_calculate)
        toolbar.addWidget(self.btn_save)
        toolbar.addWidget(self.btn_report)
        toolbar.addStretch()

        root_layout.addLayout(toolbar)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        self.original_panel = self._create_image_panel("原始图像")
        self.mask_panel = self._create_image_panel("分割掩膜")
        self.overlay_panel = self._create_image_panel("叠加结果")

        content_layout.addWidget(self.original_panel["card"])
        content_layout.addWidget(self.mask_panel["card"])
        content_layout.addWidget(self.overlay_panel["card"])

        root_layout.addLayout(content_layout, stretch=1)

        metrics_card = QFrame()
        metrics_card.setObjectName("Card")
        metrics_layout = QVBoxLayout(metrics_card)
        metrics_layout.setContentsMargins(20, 16, 20, 16)

        metric_title = QLabel("分析信息")
        metric_title.setStyleSheet("font-size: 17px; font-weight: 700; color: #111827;")
        metrics_layout.addWidget(metric_title)

        self.metrics_label = QLabel(
            "尚未导入图像。\n\n"
            "当前阶段已接入：HSV / ExG 绿色区域分割、形态学去噪、连通域过滤、掩膜与叠加图显示。"
        )
        self.metrics_label.setWordWrap(True)
        self.metrics_label.setStyleSheet("font-size: 14px; color: #374151; line-height: 1.6;")
        metrics_layout.addWidget(self.metrics_label)

        root_layout.addWidget(metrics_card)

    def _create_image_panel(self, title: str) -> dict:
        card = QFrame()
        card.setObjectName("Card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #111827;")
        layout.addWidget(title_label)

        image_label = QLabel("暂无图像")
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumHeight(340)
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
        layout.addWidget(image_label, stretch=1)

        return {
            "card": card,
            "label": image_label,
        }

    def import_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择水稻秧苗图像",
            "",
            "Image Files (*.jpg *.jpeg *.png *.bmp)"
        )

        if not file_path:
            return

        path = Path(file_path)

        image_bgr = cv2.imdecode(
            np.fromfile(str(path), dtype=np.uint8),
            cv2.IMREAD_COLOR,
        )

        if image_bgr is None:
            QMessageBox.warning(self, "图像读取失败", "无法读取该图像文件，请检查文件格式或路径。")
            return

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        self.current_image_path = path
        self.current_image_rgb = image_rgb
        self.current_segmentation = None

        self._show_ndarray_image(self.original_panel["label"], image_rgb)

        self.mask_panel["label"].setPixmap(QPixmap())
        self.mask_panel["label"].setText("待执行分割")

        self.overlay_panel["label"].setPixmap(QPixmap())
        self.overlay_panel["label"].setText("待执行分割")

        self.btn_segment.setEnabled(True)
        self.btn_calculate.setEnabled(False)
        self.btn_save.setEnabled(False)
        self.btn_report.setEnabled(False)

        height, width = image_rgb.shape[:2]

        self.metrics_label.setText(
            f"已导入图像：{path.name}\n"
            f"图像尺寸：{width} × {height} px\n"
            f"文件路径：{path}\n\n"
            "下一步：点击“执行分割”生成秧苗区域掩膜。"
        )

    def run_segmentation(self) -> None:
        if self.current_image_rgb is None:
            QMessageBox.information(self, "提示", "请先导入图像。")
            return

        config = SegmentationConfig(
            hsv_lower=(35, 40, 40),
            hsv_upper=(85, 255, 255),
            exg_threshold=30,
            min_area=300,
            kernel_size=5,
            method="HSV",
        )

        try:
            result = self.segmenter.segment(self.current_image_rgb, config)
        except Exception as exc:
            QMessageBox.critical(self, "分割失败", f"执行分割时发生错误：\n{exc}")
            return

        self.current_segmentation = result

        self._show_ndarray_image(self.mask_panel["label"], result.mask)
        self._show_ndarray_image(self.overlay_panel["label"], result.overlay)

        x, y, w, h = result.bbox

        if result.success:
            self.btn_calculate.setEnabled(True)

            self.metrics_label.setText(
                "分割完成。\n\n"
                f"分割方法：{config.method}\n"
                f"HSV 下限：{config.hsv_lower}\n"
                f"HSV 上限：{config.hsv_upper}\n"
                f"最小连通域面积：{config.min_area} px\n\n"
                f"图像有效面积：{result.valid_area_px} px\n"
                f"秧苗掩膜面积：{result.plant_area_px} px\n"
                f"外接矩形：x={x}, y={y}, w={w}, h={h}\n\n"
                "下一步：接入比例尺设置与表型指标计算。"
            )
        else:
            self.btn_calculate.setEnabled(False)

            self.metrics_label.setText(
                "分割未检测到有效区域。\n\n"
                f"提示信息：{result.message}\n\n"
                "建议：更换图像、调整拍摄背景，或后续在参数设置页中调整 HSV / ExG 阈值。"
            )

    def _show_ndarray_image(self, label: QLabel, image: np.ndarray) -> None:
        pixmap = ndarray_to_pixmap(image)

        scaled = pixmap.scaled(
            label.width(),
            label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        label.setPixmap(scaled)
        label.setText("")