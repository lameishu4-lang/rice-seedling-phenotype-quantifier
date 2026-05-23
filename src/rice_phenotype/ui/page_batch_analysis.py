# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QFileDialog,
    QDoubleSpinBox,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
)

from rice_phenotype import __version__
from rice_phenotype.core.batch import BatchAnalyzer, BatchItemResult
from rice_phenotype.core.segmentation import SegmentationConfig
from rice_phenotype.core.settings import SettingsManager
from rice_phenotype.export.excel_exporter import ResultExporter
from rice_phenotype.storage.database import RecordRepository
from rice_phenotype.utils.paths import output_dir, image_output_dir


class BatchAnalysisPage(QWidget):
    def __init__(self):
        super().__init__()

        self.current_folder: Path | None = None
        self.batch_results: list[BatchItemResult] = []

        self.last_batch_config: SegmentationConfig | None = None
        self.last_cm_per_pixel: float | None = None
        self.batch_saved = False

        self.analyzer = BatchAnalyzer()
        self.exporter = ResultExporter()
        self.settings_manager = SettingsManager()
        self.repository = RecordRepository()

        self._build_ui()
        self._load_default_scale()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(18)

        title = QLabel("批量分析")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        desc = QLabel(
            "选择图像文件夹后，软件将按照“参数设置”中的分割参数逐张执行绿色区域分割、"
            "比例尺换算和二维表型指标计算。批量分析完成后，可将成功记录保存至历史记录。"
        )
        desc.setObjectName("PageDesc")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        toolbar_card = QFrame()
        toolbar_card.setObjectName("Card")
        toolbar_layout = QHBoxLayout(toolbar_card)
        toolbar_layout.setContentsMargins(18, 12, 18, 12)
        toolbar_layout.setSpacing(12)

        self.btn_select_folder = QPushButton("选择文件夹")
        self.btn_select_folder.setObjectName("PrimaryButton")
        self.btn_select_folder.clicked.connect(self.select_folder)

        self.folder_label = QLabel("尚未选择文件夹")
        self.folder_label.setStyleSheet("font-size: 13px; color: #4B5563;")

        toolbar_layout.addWidget(self.btn_select_folder)
        toolbar_layout.addWidget(self.folder_label, stretch=1)

        layout.addWidget(toolbar_card)

        setting_card = QFrame()
        setting_card.setObjectName("Card")
        setting_layout = QHBoxLayout(setting_card)
        setting_layout.setContentsMargins(18, 12, 18, 12)
        setting_layout.setSpacing(12)

        scale_title = QLabel("统一比例尺：")
        scale_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #111827;")
        setting_layout.addWidget(scale_title)

        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setDecimals(5)
        self.scale_spin.setMinimum(0.00001)
        self.scale_spin.setMaximum(10.0)
        self.scale_spin.setSingleStep(0.001)
        self.scale_spin.setValue(0.05000)
        self.scale_spin.setSuffix(" cm/pixel")
        self.scale_spin.setFixedWidth(180)

        setting_layout.addWidget(self.scale_spin)

        self.btn_reload_settings = QPushButton("重新读取参数")
        self.btn_reload_settings.setObjectName("SecondaryButton")
        self.btn_reload_settings.clicked.connect(self.reload_settings)

        self.btn_start = QPushButton("开始批量分析")
        self.btn_start.setObjectName("PrimaryButton")
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.run_batch_analysis)

        self.btn_save_success = QPushButton("保存成功记录")
        self.btn_save_success.setObjectName("SecondaryButton")
        self.btn_save_success.setEnabled(False)
        self.btn_save_success.clicked.connect(self.save_success_records)

        self.btn_clear = QPushButton("清空结果")
        self.btn_clear.setObjectName("SecondaryButton")
        self.btn_clear.clicked.connect(self.clear_results)

        self.btn_export_excel = QPushButton("导出 Excel")
        self.btn_export_excel.setObjectName("SecondaryButton")
        self.btn_export_excel.setEnabled(False)
        self.btn_export_excel.clicked.connect(self.export_excel)

        self.btn_export_csv = QPushButton("导出 CSV")
        self.btn_export_csv.setObjectName("SecondaryButton")
        self.btn_export_csv.setEnabled(False)
        self.btn_export_csv.clicked.connect(self.export_csv)

        setting_layout.addWidget(self.btn_reload_settings)
        setting_layout.addWidget(self.btn_start)
        setting_layout.addWidget(self.btn_save_success)
        setting_layout.addWidget(self.btn_clear)
        setting_layout.addWidget(self.btn_export_excel)
        setting_layout.addWidget(self.btn_export_csv)

        setting_note = QLabel("说明：比例尺默认从“参数设置”读取，也可在本页临时修改。")
        setting_note.setStyleSheet("font-size: 13px; color: #4B5563;")
        setting_layout.addWidget(setting_note, stretch=1)

        layout.addWidget(setting_card)

        progress_card = QFrame()
        progress_card.setObjectName("Card")
        progress_layout = QVBoxLayout(progress_card)
        progress_layout.setContentsMargins(18, 14, 18, 14)
        progress_layout.setSpacing(8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

        self.status_label = QLabel("等待批量分析。")
        self.status_label.setStyleSheet("font-size: 13px; color: #4B5563;")

        self.config_label = QLabel("当前分割参数：尚未读取。")
        self.config_label.setWordWrap(True)
        self.config_label.setStyleSheet("font-size: 13px; color: #4B5563;")

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.config_label)

        layout.addWidget(progress_card)

        table_card = QFrame()
        table_card.setObjectName("Card")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(18, 16, 18, 18)
        table_layout.setSpacing(12)

        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels(
            [
                "序号",
                "样本名称",
                "状态",
                "信息",
                "株高(cm)",
                "冠幅(cm)",
                "面积(cm²)",
                "覆盖率(%)",
                "ExG",
                "Green Ratio",
                "评分",
            ]
        )

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        table_layout.addWidget(self.table)

        layout.addWidget(table_card, stretch=1)

    def _load_default_scale(self) -> None:
        settings = self.settings_manager.load()
        self.scale_spin.setValue(float(settings.default_cm_per_pixel))
        self._update_config_label()

    def _load_segmentation_config(self) -> SegmentationConfig:
        settings = self.settings_manager.load()

        return SegmentationConfig(
            hsv_lower=(
                int(settings.hsv_h_min),
                int(settings.hsv_s_min),
                int(settings.hsv_v_min),
            ),
            hsv_upper=(
                int(settings.hsv_h_max),
                int(settings.hsv_s_max),
                int(settings.hsv_v_max),
            ),
            exg_threshold=int(settings.exg_threshold),
            min_area=int(settings.min_area),
            kernel_size=int(settings.kernel_size),
            method=settings.segmentation_method,
        )

    def _update_config_label(self) -> None:
        config = self._load_segmentation_config()

        self.config_label.setText(
            "当前分割参数："
            f"方法={config.method}；"
            f"HSV下限={config.hsv_lower}；"
            f"HSV上限={config.hsv_upper}；"
            f"ExG阈值={config.exg_threshold}；"
            f"最小连通域面积={config.min_area}px；"
            f"核大小={config.kernel_size}；"
            f"比例尺={float(self.scale_spin.value()):.5f} cm/pixel。"
        )

    def reload_settings(self) -> None:
        self._load_default_scale()
        self._update_config_label()

        QMessageBox.information(
            self,
            "读取成功",
            "已重新读取“参数设置”页保存的默认比例尺和分割参数。"
        )

    def select_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择包含水稻秧苗图像的文件夹",
            "",
        )

        if not folder:
            return

        self._load_default_scale()
        self.current_folder = Path(folder)
        self.folder_label.setText(str(self.current_folder))
        self.btn_start.setEnabled(True)

        self.batch_results = []
        self.table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.batch_saved = False
        self.btn_save_success.setEnabled(False)
        self.btn_export_excel.setEnabled(False)
        self.btn_export_csv.setEnabled(False)

        try:
            image_paths = self.analyzer.list_images(self.current_folder)
        except Exception as exc:
            QMessageBox.warning(self, "文件夹读取失败", str(exc))
            self.btn_start.setEnabled(False)
            return

        self.status_label.setText(
            f"已选择文件夹，共识别到 {len(image_paths)} 张支持格式图像。"
        )
        self._update_config_label()

        if len(image_paths) == 0:
            self.btn_start.setEnabled(False)
            QMessageBox.information(
                self,
                "未发现图像",
                "该文件夹中未发现 JPG、PNG 或 BMP 图像。"
            )

    def run_batch_analysis(self) -> None:
        if self.current_folder is None:
            QMessageBox.information(self, "提示", "请先选择图像文件夹。")
            return

        cm_per_pixel = float(self.scale_spin.value())

        if cm_per_pixel <= 0:
            QMessageBox.warning(self, "比例尺错误", "比例尺必须大于 0。")
            return

        try:
            image_paths = self.analyzer.list_images(self.current_folder)
        except Exception as exc:
            QMessageBox.warning(self, "文件夹读取失败", str(exc))
            return

        if not image_paths:
            QMessageBox.information(self, "提示", "当前文件夹中没有可分析图像。")
            return

        config = self._load_segmentation_config()
        self._update_config_label()

        self.last_batch_config = config
        self.last_cm_per_pixel = cm_per_pixel
        self.batch_saved = False

        self.btn_start.setEnabled(False)
        self.btn_save_success.setEnabled(False)
        self.btn_export_excel.setEnabled(False)
        self.btn_export_csv.setEnabled(False)

        self.progress_bar.setValue(0)
        self.batch_results = []
        self.table.setRowCount(0)

        total = len(image_paths)

        for index, image_path in enumerate(image_paths, start=1):
            self.status_label.setText(
                f"正在分析 {index}/{total}：{image_path.name}"
            )

            result = self.analyzer.analyze_single_image(
                image_path=image_path,
                cm_per_pixel=cm_per_pixel,
                config=config,
            )

            self.batch_results.append(result)
            self._append_result_row(index, result)

            progress = int(index / total * 100)
            self.progress_bar.setValue(progress)

            self.repaint()

        success_count = sum(1 for item in self.batch_results if item.success)
        fail_count = len(self.batch_results) - success_count

        self.status_label.setText(
            f"批量分析完成：成功 {success_count} 张，失败 {fail_count} 张。"
        )

        self.btn_start.setEnabled(True)
        self.btn_save_success.setEnabled(success_count > 0)
        self.btn_export_excel.setEnabled(len(self.batch_results) > 0)
        self.btn_export_csv.setEnabled(len(self.batch_results) > 0)

    def _append_result_row(
        self,
        index: int,
        result: BatchItemResult,
    ) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)

        metrics = result.metrics

        values = [
            index,
            result.sample_name,
            "成功" if result.success else "失败",
            result.message,
            self._format_float(metrics.plant_height_cm, 2) if metrics else "",
            self._format_float(metrics.canopy_width_cm, 2) if metrics else "",
            self._format_float(metrics.projected_area_cm2, 2) if metrics else "",
            self._format_percent(metrics.green_coverage) if metrics else "",
            self._format_float(metrics.exg_mean, 2) if metrics else "",
            self._format_float(metrics.green_ratio, 4) if metrics else "",
            self._format_float(metrics.growth_score, 2) if metrics else "",
        ]

        for col_index, value in enumerate(values):
            item = QTableWidgetItem(str(value))

            if col_index in [0, 2]:
                item.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(row, col_index, item)

    def save_success_records(self) -> None:
        if not self.batch_results:
            QMessageBox.information(self, "提示", "暂无可保存的批量分析结果。")
            return

        if self.batch_saved:
            QMessageBox.information(self, "提示", "当前批量分析结果已经保存过成功记录。")
            self.btn_save_success.setEnabled(False)
            return

        success_items = [
            item for item in self.batch_results
            if item.success and item.metrics is not None and item.mask is not None and item.overlay is not None
        ]

        if not success_items:
            QMessageBox.information(self, "提示", "当前批量分析结果中没有可保存的成功记录。")
            return

        if self.last_batch_config is None or self.last_cm_per_pixel is None:
            QMessageBox.warning(self, "提示", "缺少本次批量分析参数，无法保存记录。")
            return

        reply = QMessageBox.question(
            self,
            "确认保存",
            (
                f"将保存 {len(success_items)} 条成功分析记录到历史记录。\n\n"
                "失败项不会保存。\n"
                "保存后同一轮批量结果不能重复保存。\n\n"
                "是否继续？"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        saved_count = 0
        failed_count = 0
        first_error = ""

        save_time = datetime.now()
        timestamp = save_time.strftime("%Y%m%d_%H%M%S")
        output_folder = image_output_dir()

        config = self.last_batch_config
        cm_per_pixel = float(self.last_cm_per_pixel)

        for index, item in enumerate(success_items, start=1):
            try:
                base_name = item.image_path.stem
                mask_path = output_folder / f"{base_name}_{timestamp}_batch_{index:03d}_mask.png"
                overlay_path = output_folder / f"{base_name}_{timestamp}_batch_{index:03d}_overlay.png"

                self._save_mask_image(mask_path, item.mask)
                self._save_rgb_image(overlay_path, item.overlay)

                metrics = item.metrics

                record = {
                    "sample_name": item.sample_name,
                    "image_path": str(item.image_path),
                    "mask_path": str(mask_path),
                    "overlay_path": str(overlay_path),
                    "analysis_time": save_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "image_width": item.image_width,
                    "image_height": item.image_height,
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
                    "note": "批量分析保存",
                    "software_version": __version__,
                }

                self.repository.insert_record(record)
                saved_count += 1

            except Exception as exc:
                failed_count += 1

                if not first_error:
                    first_error = str(exc)

        if saved_count > 0:
            self.batch_saved = True
            self.btn_save_success.setEnabled(False)

        message = f"批量成功记录保存完成。\n成功保存：{saved_count} 条\n保存失败：{failed_count} 条"

        if first_error:
            message += f"\n\n首个错误：{first_error}"

        QMessageBox.information(self, "保存结果", message)

    def export_excel(self) -> None:
        if not self.batch_results:
            QMessageBox.information(self, "提示", "暂无可导出的批量分析结果。")
            return

        default_name = f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        default_path = output_dir() / default_name

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出批量分析结果 Excel",
            str(default_path),
            "Excel Files (*.xlsx)",
        )

        if not file_path:
            return

        try:
            output_path = self.exporter.export_batch_results_to_excel(
                self.batch_results,
                Path(file_path),
            )
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", f"导出 Excel 时发生错误：\n{exc}")
            return

        QMessageBox.information(self, "导出成功", f"批量分析结果已导出：\n{output_path}")

    def export_csv(self) -> None:
        if not self.batch_results:
            QMessageBox.information(self, "提示", "暂无可导出的批量分析结果。")
            return

        default_name = f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        default_path = output_dir() / default_name

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出批量分析结果 CSV",
            str(default_path),
            "CSV Files (*.csv)",
        )

        if not file_path:
            return

        try:
            output_path = self.exporter.export_batch_results_to_csv(
                self.batch_results,
                Path(file_path),
            )
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", f"导出 CSV 时发生错误：\n{exc}")
            return

        QMessageBox.information(self, "导出成功", f"批量分析结果已导出：\n{output_path}")

    def clear_results(self) -> None:
        self.batch_results = []
        self.table.setRowCount(0)
        self.progress_bar.setValue(0)

        self.last_batch_config = None
        self.last_cm_per_pixel = None
        self.batch_saved = False

        self.status_label.setText("已清空批量分析结果。")
        self.btn_save_success.setEnabled(False)
        self.btn_export_excel.setEnabled(False)
        self.btn_export_csv.setEnabled(False)
        self._update_config_label()

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

    @staticmethod
    def _format_float(value, digits: int) -> str:
        if value is None:
            return ""

        try:
            return f"{float(value):.{digits}f}"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _format_percent(value) -> str:
        if value is None:
            return ""

        try:
            return f"{float(value) * 100:.2f}"
        except (TypeError, ValueError):
            return str(value)