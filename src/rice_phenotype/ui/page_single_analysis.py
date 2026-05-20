# -*- coding: utf-8 -*-

from datetime import datetime
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
    QDoubleSpinBox,
)

from rice_phenotype import __version__
from rice_phenotype.core.segmentation import (
    SeedlingSegmenter,
    SegmentationConfig,
    SegmentationResult,
)
from rice_phenotype.core.calibration import ScaleCalibrator
from rice_phenotype.core.metrics import PhenotypeCalculator, PhenotypeMetrics
from rice_phenotype.storage.database import RecordRepository
from rice_phenotype.utils.image_qt import ndarray_to_pixmap
from rice_phenotype.utils.paths import image_output_dir


class SingleAnalysisPage(QWidget):
    def __init__(self):
        super().__init__()

        self.current_image_path: Path | None = None
        self.current_image_rgb: np.ndarray | None = None
        self.current_segmentation: SegmentationResult | None = None
        self.current_metrics: PhenotypeMetrics | None = None
        self.current_config: SegmentationConfig | None = None

        self.segmenter = SeedlingSegmenter()
        self.calibrator = ScaleCalibrator()
        self.calculator = PhenotypeCalculator()
        self.repository = RecordRepository()

        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(36, 32, 36, 32)
        root_layout.setSpacing(18)

        title = QLabel("单张图像分析")
        title.setObjectName("PageTitle")
        root_layout.addWidget(title)

        desc = QLabel(
            "导入水稻秧苗图像，完成绿色植株区域分割、比例尺换算和二维表型指标计算。"
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
        self.btn_calculate.clicked.connect(self.calculate_metrics)

        self.btn_save = QPushButton("保存记录")
        self.btn_save.setObjectName("SecondaryButton")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_record)

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

        scale_card = QFrame()
        scale_card.setObjectName("Card")
        scale_layout = QHBoxLayout(scale_card)
        scale_layout.setContentsMargins(18, 12, 18, 12)
        scale_layout.setSpacing(12)

        scale_title = QLabel("比例尺设置：")
        scale_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #111827;")
        scale_layout.addWidget(scale_title)

        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setDecimals(5)
        self.scale_spin.setMinimum(0.00001)
        self.scale_spin.setMaximum(10.0)
        self.scale_spin.setSingleStep(0.001)
        self.scale_spin.setValue(0.05000)
        self.scale_spin.setSuffix(" cm/pixel")
        self.scale_spin.setFixedWidth(180)
        scale_layout.addWidget(self.scale_spin)

        scale_note = QLabel("说明：当前采用手动比例尺，结果用于二维图像辅助量化。")
        scale_note.setStyleSheet("font-size: 13px; color: #4B5563;")
        scale_layout.addWidget(scale_note)
        scale_layout.addStretch()

        root_layout.addWidget(scale_card)

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

        metric_title = QLabel("分析信息与表型指标")
        metric_title.setStyleSheet("font-size: 17px; font-weight: 700; color: #111827;")
        metrics_layout.addWidget(metric_title)

        self.metrics_label = QLabel(
            "尚未导入图像。\n\n"
            "当前页面支持：图像导入、绿色区域分割、比例尺换算、株高估算、冠幅估算、"
            "投影面积、绿色覆盖率、叶色指数和软件内部长势评分。"
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
        image_label.setMinimumHeight(320)
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
        self.current_metrics = None
        self.current_config = None

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
        self.current_config = config
        self.current_metrics = None

        self._show_ndarray_image(self.mask_panel["label"], result.mask)
        self._show_ndarray_image(self.overlay_panel["label"], result.overlay)

        x, y, w, h = result.bbox

        if result.success:
            self.btn_calculate.setEnabled(True)
            self.btn_save.setEnabled(False)
            self.btn_report.setEnabled(False)

            self.metrics_label.setText(
                "分割完成。\n\n"
                f"分割方法：{config.method}\n"
                f"HSV 下限：{config.hsv_lower}\n"
                f"HSV 上限：{config.hsv_upper}\n"
                f"最小连通域面积：{config.min_area} px\n\n"
                f"图像有效面积：{result.valid_area_px} px\n"
                f"秧苗掩膜面积：{result.plant_area_px} px\n"
                f"外接矩形：x={x}, y={y}, w={w}, h={h}\n\n"
                "下一步：确认比例尺后，点击“计算指标”。"
            )
        else:
            self.btn_calculate.setEnabled(False)
            self.btn_save.setEnabled(False)
            self.btn_report.setEnabled(False)

            self.metrics_label.setText(
                "分割未检测到有效区域。\n\n"
                f"提示信息：{result.message}\n\n"
                "建议：更换图像、调整拍摄背景，或后续在参数设置页中调整 HSV / ExG 阈值。"
            )

    def calculate_metrics(self) -> None:
        if self.current_image_rgb is None:
            QMessageBox.information(self, "提示", "请先导入图像。")
            return

        if self.current_segmentation is None or not self.current_segmentation.success:
            QMessageBox.information(self, "提示", "请先完成有效分割。")
            return

        cm_per_pixel = float(self.scale_spin.value())

        try:
            self.calibrator.validate_cm_per_pixel(cm_per_pixel)

            metrics = self.calculator.calculate(
                image_rgb=self.current_image_rgb,
                mask=self.current_segmentation.mask,
                cm_per_pixel=cm_per_pixel,
                valid_area_px=self.current_segmentation.valid_area_px,
            )

        except Exception as exc:
            QMessageBox.critical(self, "指标计算失败", f"计算表型指标时发生错误：\n{exc}")
            return

        self.current_metrics = metrics

        self.metrics_label.setText(self._format_metrics(metrics, cm_per_pixel))

        self.btn_save.setEnabled(True)
        self.btn_report.setEnabled(False)

    def save_record(self) -> None:
        if self.current_image_path is None:
            QMessageBox.information(self, "提示", "请先导入图像。")
            return

        if self.current_image_rgb is None:
            QMessageBox.information(self, "提示", "当前图像为空。")
            return

        if self.current_segmentation is None or not self.current_segmentation.success:
            QMessageBox.information(self, "提示", "请先完成有效分割。")
            return

        if self.current_metrics is None:
            QMessageBox.information(self, "提示", "请先计算表型指标。")
            return

        if self.current_config is None:
            QMessageBox.information(self, "提示", "缺少分割参数。")
            return

        try:
            save_time = datetime.now()
            timestamp = save_time.strftime("%Y%m%d_%H%M%S")
            base_name = self.current_image_path.stem

            output_folder = image_output_dir()

            mask_path = output_folder / f"{base_name}_{timestamp}_mask.png"
            overlay_path = output_folder / f"{base_name}_{timestamp}_overlay.png"

            self._save_mask_image(mask_path, self.current_segmentation.mask)
            self._save_rgb_image(overlay_path, self.current_segmentation.overlay)

            height, width = self.current_image_rgb.shape[:2]
            metrics = self.current_metrics
            config = self.current_config
            cm_per_pixel = float(self.scale_spin.value())

            record = {
                "sample_name": self.current_image_path.name,
                "image_path": str(self.current_image_path),
                "mask_path": str(mask_path),
                "overlay_path": str(overlay_path),
                "analysis_time": save_time.strftime("%Y-%m-%d %H:%M:%S"),
                "image_width": width,
                "image_height": height,
                "cm_per_pixel": cm_per_pixel,
                "segmentation_method": config.method,
                "hsv_lower": str(config.hsv_lower),
                "hsv_upper": str(config.hsv_upper),
                "exg_threshold": config.exg_threshold,
                "plant_height_px": metrics.plant_height_px,
                "plant_height_cm": metrics.plant_height_cm,
                "canopy_width_px": metrics.canopy_width_px,
                "canopy_width_cm": metrics.canopy_width_cm,
                "projected_area_px": metrics.projected_area_px,
                "projected_area_cm2": metrics.projected_area_cm2,
                "green_coverage": metrics.green_coverage,
                "exg_mean": metrics.exg_mean,
                "green_ratio": metrics.green_ratio,
                "bbox_fill_ratio": metrics.bbox_fill_ratio,
                "growth_score": metrics.growth_score,
                "note": "",
                "software_version": __version__,
            }

            record_id = self.repository.insert_record(record)

        except Exception as exc:
            QMessageBox.critical(self, "保存失败", f"保存分析记录时发生错误：\n{exc}")
            return

        QMessageBox.information(
            self,
            "保存成功",
            f"分析记录已保存。\n记录编号：{record_id}"
        )

        self.btn_save.setEnabled(False)

    def _format_metrics(
        self,
        metrics: PhenotypeMetrics,
        cm_per_pixel: float,
    ) -> str:
        return (
            "表型指标计算完成。\n\n"
            f"当前比例尺：{cm_per_pixel:.5f} cm/pixel\n\n"
            "【形态指标】\n"
            f"株高估算：{metrics.plant_height_cm:.2f} cm "
            f"({metrics.plant_height_px:.0f} px)\n"
            f"冠幅估算：{metrics.canopy_width_cm:.2f} cm "
            f"({metrics.canopy_width_px:.0f} px)\n"
            f"投影面积：{metrics.projected_area_cm2:.2f} cm² "
            f"({metrics.projected_area_px:.0f} px)\n"
            f"绿色覆盖率：{metrics.green_coverage * 100:.2f}%\n\n"
            "【颜色指标】\n"
            f"ExG 叶色指数均值：{metrics.exg_mean:.2f}\n"
            f"Green Ratio：{metrics.green_ratio:.4f}\n\n"
            "【软件内部评分】\n"
            f"掩膜外接矩形填充率：{metrics.bbox_fill_ratio * 100:.2f}%\n"
            f"长势评分：{metrics.growth_score:.2f} / 100\n\n"
            "说明：以上结果基于二维图像分割和比例尺换算，仅用于样本记录、"
            "教学演示和科研辅助整理，不作为农学诊断或生产决策依据。"
        )

    def _show_ndarray_image(self, label: QLabel, image: np.ndarray) -> None:
        pixmap = ndarray_to_pixmap(image)

        target_width = max(label.width(), 320)
        target_height = max(label.height(), 260)

        scaled = pixmap.scaled(
            target_width,
            target_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        label.setPixmap(scaled)
        label.setText("")

    @staticmethod
    def _save_mask_image(path: Path, mask: np.ndarray) -> None:
        success, encoded = cv2.imencode(".png", mask)

        if not success:
            raise RuntimeError("掩膜图编码失败。")

        encoded.tofile(str(path))

    @staticmethod
    def _save_rgb_image(path: Path, image_rgb: np.ndarray) -> None:
        image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

        success, encoded = cv2.imencode(".png", image_bgr)

        if not success:
            raise RuntimeError("图像编码失败。")

        encoded.tofile(str(path))