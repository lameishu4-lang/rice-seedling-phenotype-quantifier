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
    QScrollArea,
)

from rice_phenotype import __version__
from rice_phenotype.core.batch import BatchAnalyzer, BatchItemResult
from rice_phenotype.core.segmentation import SegmentationConfig
from rice_phenotype.core.settings import SettingsManager
from rice_phenotype.core.statistics import BatchStatisticsCalculator, BatchSummary
from rice_phenotype.export.excel_exporter import ResultExporter
from rice_phenotype.storage.database import RecordRepository
from rice_phenotype.ui.widgets.charts import BarChartWidget, ScoreLevelWidget
from rice_phenotype.ui.dialogs.sample_review_dialog import SampleReviewDialog
from rice_phenotype.utils.paths import output_dir, image_output_dir


class BatchAnalysisPage(QWidget):
    def __init__(self):
        super().__init__()

        self.current_folder: Path | None = None
        self.batch_results: list[BatchItemResult] = []
        self.current_summary: BatchSummary | None = None

        self.last_batch_config: SegmentationConfig | None = None
        self.last_cm_per_pixel: float | None = None
        self.batch_saved = False

        self.analyzer = BatchAnalyzer()
        self.exporter = ResultExporter()
        self.settings_manager = SettingsManager()
        self.repository = RecordRepository()
        self.summary_calculator = BatchStatisticsCalculator()

        self._build_ui()
        self._load_default_scale()
        self._reset_visualization()

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(18)

        scroll_area.setWidget(content)
        outer_layout.addWidget(scroll_area)

        title = QLabel("批量分析")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        desc = QLabel(
            "选择图像文件夹后，软件将按照“参数设置”中的分割参数逐张执行绿色区域分割、"
            "比例尺换算和二维表型指标计算。批量分析完成后，可查看统计摘要、解释提示、"
            "可视化结果、保存成功记录、复核单个样本或导出结果。"
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

        self.btn_review_sample = QPushButton("查看选中样本")
        self.btn_review_sample.setObjectName("SecondaryButton")
        self.btn_review_sample.setEnabled(False)
        self.btn_review_sample.clicked.connect(self.review_selected_sample)

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
        setting_layout.addWidget(self.btn_review_sample)
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

        summary_card = QFrame()
        summary_card.setObjectName("Card")
        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(18, 14, 18, 14)
        summary_layout.setSpacing(8)

        summary_title = QLabel("批量统计摘要")
        summary_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #111827;")
        summary_layout.addWidget(summary_title)

        self.summary_label = QLabel("尚未进行批量分析。")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("font-size: 13px; color: #374151; line-height: 1.6;")
        summary_layout.addWidget(self.summary_label)

        layout.addWidget(summary_card)

        insight_card = QFrame()
        insight_card.setObjectName("Card")
        insight_layout = QVBoxLayout(insight_card)
        insight_layout.setContentsMargins(18, 14, 18, 14)
        insight_layout.setSpacing(8)

        insight_title = QLabel("批量结果解释提示")
        insight_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #111827;")
        insight_layout.addWidget(insight_title)

        self.insight_label = QLabel("尚未生成批量结果解释提示。")
        self.insight_label.setWordWrap(True)
        self.insight_label.setStyleSheet("font-size: 13px; color: #374151; line-height: 1.6;")
        insight_layout.addWidget(self.insight_label)

        insight_note = QLabel(
            "说明：解释提示基于软件内部评分和二维图像指标生成，仅用于辅助查看和复核，"
            "不作为农学诊断或生产决策依据。"
        )
        insight_note.setWordWrap(True)
        insight_note.setStyleSheet("font-size: 12px; color: #6B7280;")
        insight_layout.addWidget(insight_note)

        layout.addWidget(insight_card)

        visual_card = QFrame()
        visual_card.setObjectName("Card")
        visual_card.setMinimumHeight(330)
        visual_layout = QVBoxLayout(visual_card)
        visual_layout.setContentsMargins(18, 14, 18, 14)
        visual_layout.setSpacing(10)

        visual_title = QLabel("批量结果可视化")
        visual_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #111827;")
        visual_layout.addWidget(visual_title)

        chart_layout = QHBoxLayout()
        chart_layout.setSpacing(12)

        self.score_chart = BarChartWidget("长势评分柱状图")
        self.height_chart = BarChartWidget("株高估算柱状图")
        self.score_level_widget = ScoreLevelWidget("评分等级统计")

        chart_layout.addWidget(self.score_chart, stretch=1)
        chart_layout.addWidget(self.height_chart, stretch=1)
        chart_layout.addWidget(self.score_level_widget, stretch=1)

        visual_layout.addLayout(chart_layout)

        visual_note = QLabel(
            "说明：柱状图横轴为样本序号，对应下方结果明细表；"
            "图表仅用于批量样本间的相对比较，评分等级为软件内部评分分级，不作为农学诊断结论。"
        )
        visual_note.setWordWrap(True)
        visual_note.setStyleSheet("font-size: 12px; color: #6B7280;")
        visual_layout.addWidget(visual_note)

        layout.addWidget(visual_card)

        table_card = QFrame()
        table_card.setObjectName("Card")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(18, 16, 18, 18)
        table_layout.setSpacing(12)

        table_title = QLabel("批量结果明细")
        table_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #111827;")
        table_layout.addWidget(table_title)

        self.table = QTableWidget()
        self.table.setMinimumHeight(420)
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
        self.table.itemSelectionChanged.connect(self._update_review_button_state)

        table_layout.addWidget(self.table)

        layout.addWidget(table_card)
        layout.addStretch()

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
        self.current_summary = None
        self.table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.batch_saved = False

        self.btn_save_success.setEnabled(False)
        self.btn_review_sample.setEnabled(False)
        self.btn_export_excel.setEnabled(False)
        self.btn_export_csv.setEnabled(False)

        self.summary_label.setText("尚未进行批量分析。")
        self.insight_label.setText("尚未生成批量结果解释提示。")
        self._reset_visualization()

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
        self.btn_review_sample.setEnabled(False)
        self.btn_export_excel.setEnabled(False)
        self.btn_export_csv.setEnabled(False)

        self.progress_bar.setValue(0)
        self.batch_results = []
        self.current_summary = None
        self.table.setRowCount(0)
        self.summary_label.setText("正在统计批量分析结果...")
        self.insight_label.setText("正在生成批量结果解释提示...")
        self._reset_visualization()

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

        self.current_summary = self.summary_calculator.calculate(self.batch_results)
        self.summary_label.setText(self._format_summary(self.current_summary))
        self.insight_label.setText(self._format_insights(self.current_summary, self.batch_results))
        self._update_visualization()

        success_count = self.current_summary.success_count
        fail_count = self.current_summary.failed_count

        self.status_label.setText(
            f"批量分析完成：成功 {success_count} 张，失败 {fail_count} 张。"
        )

        self.btn_start.setEnabled(True)
        self.btn_save_success.setEnabled(success_count > 0)
        self.btn_export_excel.setEnabled(len(self.batch_results) > 0)
        self.btn_export_csv.setEnabled(len(self.batch_results) > 0)

        if self.batch_results:
            self.table.selectRow(0)

        self._update_review_button_state()

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

    def _reset_visualization(self) -> None:
        self.score_chart.set_data("长势评分柱状图", [], [], "")
        self.height_chart.set_data("株高估算柱状图", [], [], " cm")
        self.score_level_widget.set_scores([])

    def _update_visualization(self) -> None:
        success_items = [
            item for item in self.batch_results
            if item.success and item.metrics is not None
        ]

        labels = [item.sample_name for item in success_items]
        scores = [float(item.metrics.growth_score) for item in success_items]
        heights = [float(item.metrics.plant_height_cm) for item in success_items]

        self.score_chart.set_data(
            title="长势评分柱状图",
            labels=labels,
            values=scores,
            unit="",
            max_items=30,
        )

        self.height_chart.set_data(
            title="株高估算柱状图",
            labels=labels,
            values=heights,
            unit=" cm",
            max_items=30,
        )

        self.score_level_widget.set_scores(scores)

    def _update_review_button_state(self) -> None:
        if not self.batch_results:
            self.btn_review_sample.setEnabled(False)
            return

        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            self.btn_review_sample.setEnabled(False)
            return

        row_index = selected_rows[0].row()
        self.btn_review_sample.setEnabled(0 <= row_index < len(self.batch_results))

    def review_selected_sample(self) -> None:
        if not self.batch_results:
            QMessageBox.information(self, "提示", "暂无可复核的批量分析结果。")
            return

        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.information(self, "提示", "请先在结果明细表中选择一条样本记录。")
            return

        row_index = selected_rows[0].row()

        if row_index < 0 or row_index >= len(self.batch_results):
            QMessageBox.warning(self, "提示", "选中的样本序号无效。")
            return

        result = self.batch_results[row_index]

        dialog = SampleReviewDialog(
            sample_index=row_index + 1,
            result=result,
            cm_per_pixel=self.last_cm_per_pixel,
            parent=self,
        )
        dialog.exec()

    def _format_insights(
        self,
        summary: BatchSummary,
        results: list[BatchItemResult],
    ) -> str:
        if summary.total_count == 0:
            return "当前没有可解释的批量分析结果。"

        success_items_with_index = [
            (index, item)
            for index, item in enumerate(results, start=1)
            if item.success and item.metrics is not None
        ]

        if not success_items_with_index:
            return (
                "当前批量分析未得到成功样本。建议检查图像格式、图像质量、拍摄背景，"
                "或在“参数设置”中调整分割参数后重新分析。"
            )

        scores = [
            (index, item.sample_name, float(item.metrics.growth_score))
            for index, item in success_items_with_index
        ]

        scores_sorted = sorted(scores, key=lambda item: item[2])
        lowest_index, _, lowest_score = scores_sorted[0]
        highest_index, _, highest_score = scores_sorted[-1]

        low_score_items = [
            item for item in scores
            if item[2] < 60
        ]

        high_score_items = [
            item for item in scores
            if item[2] >= 80
        ]

        lines = [
            f"本批次共分析 {summary.total_count} 张图像，成功 {summary.success_count} 张，失败 {summary.failed_count} 张，成功率 {summary.success_rate * 100:.2f}%。",
            f"最高评分样本为第 {highest_index} 号（{highest_score:.2f}），最低评分样本为第 {lowest_index} 号（{lowest_score:.2f}）。",
        ]

        if low_score_items:
            lines.append(
                f"本批次有 {len(low_score_items)} 个样本评分低于 60，建议优先复核这些样本的图像质量、分割效果和实际秧苗状态。"
            )

            preview_items = low_score_items[:5]
            preview_text = "；".join(
                f"第 {index} 号 {score:.2f}"
                for index, _, score in preview_items
            )

            if len(low_score_items) > 5:
                preview_text += "；..."

            lines.append(f"低评分样本提示：{preview_text}。")
        else:
            lines.append(
                "本批次未出现评分低于 60 的样本，可结合明细表继续查看各样本之间的相对差异。"
            )

        if high_score_items:
            lines.append(
                f"评分不低于 80 的样本共 {len(high_score_items)} 个，可作为本批次相对较高评分样本进行对照查看。"
            )

        if summary.failed_count > 0:
            lines.append(
                "存在分析失败图像，建议查看明细表中的失败原因，并检查文件格式、图像读取情况或分割参数。"
            )

        lines.append(
            "上述提示仅基于二维图像指标和软件内部评分生成，用于辅助筛查和复核，不作为农学诊断、品种评价或生产决策依据。"
        )

        return "\n".join(lines)

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
            if item.success
            and item.metrics is not None
            and getattr(item, "mask", None) is not None
            and getattr(item, "overlay", None) is not None
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
        self.current_summary = None
        self.table.setRowCount(0)
        self.progress_bar.setValue(0)

        self.last_batch_config = None
        self.last_cm_per_pixel = None
        self.batch_saved = False

        self.status_label.setText("已清空批量分析结果。")
        self.summary_label.setText("尚未进行批量分析。")
        self.insight_label.setText("尚未生成批量结果解释提示。")

        self.btn_save_success.setEnabled(False)
        self.btn_review_sample.setEnabled(False)
        self.btn_export_excel.setEnabled(False)
        self.btn_export_csv.setEnabled(False)

        self._reset_visualization()
        self._update_config_label()

    def _format_summary(self, summary: BatchSummary) -> str:
        return (
            f"样本总数：{summary.total_count}；"
            f"成功：{summary.success_count}；"
            f"失败：{summary.failed_count}；"
            f"成功率：{summary.success_rate * 100:.2f}%\n\n"
            "【株高】"
            f"均值 {self._format_metric(summary.plant_height_cm.mean_value, 2)} cm，"
            f"最小 {self._format_metric(summary.plant_height_cm.min_value, 2)} cm，"
            f"最大 {self._format_metric(summary.plant_height_cm.max_value, 2)} cm\n"
            "【冠幅】"
            f"均值 {self._format_metric(summary.canopy_width_cm.mean_value, 2)} cm，"
            f"最小 {self._format_metric(summary.canopy_width_cm.min_value, 2)} cm，"
            f"最大 {self._format_metric(summary.canopy_width_cm.max_value, 2)} cm\n"
            "【投影面积】"
            f"均值 {self._format_metric(summary.projected_area_cm2.mean_value, 2)} cm²，"
            f"最小 {self._format_metric(summary.projected_area_cm2.min_value, 2)} cm²，"
            f"最大 {self._format_metric(summary.projected_area_cm2.max_value, 2)} cm²\n"
            "【绿色覆盖率】"
            f"均值 {self._format_percent_value(summary.green_coverage.mean_value)}，"
            f"最小 {self._format_percent_value(summary.green_coverage.min_value)}，"
            f"最大 {self._format_percent_value(summary.green_coverage.max_value)}\n"
            "【长势评分】"
            f"均值 {self._format_metric(summary.growth_score.mean_value, 2)}，"
            f"最小 {self._format_metric(summary.growth_score.min_value, 2)}，"
            f"最大 {self._format_metric(summary.growth_score.max_value, 2)}"
        )

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
    def _format_metric(value, digits: int) -> str:
        if value is None:
            return "-"

        try:
            return f"{float(value):.{digits}f}"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _format_percent_value(value) -> str:
        if value is None:
            return "-"

        try:
            return f"{float(value) * 100:.2f}%"
        except (TypeError, ValueError):
            return str(value)

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