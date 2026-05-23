# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QInputDialog,
    QHeaderView,
    QFileDialog,
)

from rice_phenotype.storage.database import RecordRepository
from rice_phenotype.export.excel_exporter import ResultExporter
from rice_phenotype.ui.dialogs.record_review_dialog import RecordReviewDialog
from rice_phenotype.utils.paths import output_dir


class RecordsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.repository = RecordRepository()
        self.exporter = ResultExporter()
        self.records: list[dict] = []

        self._build_ui()
        self.refresh_records()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(18)

        title = QLabel("历史记录")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        desc = QLabel(
            "本页用于查看、查询、复核、备注、删除、导出和管理历史分析记录。"
            "表格序号为当前查询结果的连续显示序号，数据库内部记录ID仅用于数据追踪。"
        )
        desc.setObjectName("PageDesc")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        toolbar_card = QFrame()
        toolbar_card.setObjectName("Card")
        toolbar_layout = QHBoxLayout(toolbar_card)
        toolbar_layout.setContentsMargins(18, 12, 18, 12)
        toolbar_layout.setSpacing(12)

        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入样本名称或备注关键词")
        self.keyword_input.setFixedWidth(280)

        self.btn_search = QPushButton("查询")
        self.btn_search.setObjectName("PrimaryButton")
        self.btn_search.clicked.connect(self.refresh_records)

        self.btn_reset = QPushButton("重置")
        self.btn_reset.setObjectName("SecondaryButton")
        self.btn_reset.clicked.connect(self.reset_search)

        self.btn_review = QPushButton("查看记录详情")
        self.btn_review.setObjectName("SecondaryButton")
        self.btn_review.setEnabled(False)
        self.btn_review.clicked.connect(self.review_selected_record)

        self.btn_note = QPushButton("编辑备注")
        self.btn_note.setObjectName("SecondaryButton")
        self.btn_note.clicked.connect(self.edit_note)

        self.btn_delete = QPushButton("删除记录")
        self.btn_delete.setObjectName("SecondaryButton")
        self.btn_delete.clicked.connect(self.delete_selected_record)

        self.btn_export_excel = QPushButton("导出 Excel")
        self.btn_export_excel.setObjectName("SecondaryButton")
        self.btn_export_excel.clicked.connect(self.export_excel)

        self.btn_export_csv = QPushButton("导出 CSV")
        self.btn_export_csv.setObjectName("SecondaryButton")
        self.btn_export_csv.clicked.connect(self.export_csv)

        toolbar_layout.addWidget(QLabel("记录查询："))
        toolbar_layout.addWidget(self.keyword_input)
        toolbar_layout.addWidget(self.btn_search)
        toolbar_layout.addWidget(self.btn_reset)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_review)
        toolbar_layout.addWidget(self.btn_note)
        toolbar_layout.addWidget(self.btn_delete)
        toolbar_layout.addWidget(self.btn_export_excel)
        toolbar_layout.addWidget(self.btn_export_csv)

        layout.addWidget(toolbar_card)

        summary_card = QFrame()
        summary_card.setObjectName("Card")
        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(18, 14, 18, 14)
        summary_layout.setSpacing(8)

        summary_title = QLabel("历史记录统计摘要")
        summary_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #111827;")
        summary_layout.addWidget(summary_title)

        self.summary_label = QLabel("暂无历史记录统计信息。")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("font-size: 13px; color: #374151; line-height: 1.6;")
        summary_layout.addWidget(self.summary_label)

        layout.addWidget(summary_card)

        table_card = QFrame()
        table_card.setObjectName("Card")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(18, 16, 18, 18)
        table_layout.setSpacing(12)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            [
                "序号",
                "样本名称",
                "分析时间",
                "比例尺(cm/px)",
                "株高(cm)",
                "冠幅(cm)",
                "面积(cm²)",
                "覆盖率(%)",
                "评分",
                "备注",
            ]
        )

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.itemSelectionChanged.connect(self.update_detail)
        self.table.itemSelectionChanged.connect(self._update_action_buttons)

        table_layout.addWidget(self.table)

        self.detail_label = QLabel("请选择一条记录查看摘要。")
        self.detail_label.setWordWrap(True)
        self.detail_label.setStyleSheet("font-size: 13px; color: #4B5563;")
        table_layout.addWidget(self.detail_label)

        layout.addWidget(table_card, stretch=1)

    def refresh_records(self) -> None:
        keyword = self.keyword_input.text().strip()
        self.records = self.repository.query_records(keyword=keyword)
        self._fill_table(self.records)
        self._update_summary(self.records)
        self._update_action_buttons()

    def reset_search(self) -> None:
        self.keyword_input.clear()
        self.refresh_records()

    def _fill_table(self, records: list[dict]) -> None:
        self.table.setRowCount(len(records))

        for row_index, record in enumerate(records):
            display_index = row_index + 1
            record_id = record.get("id")

            values = [
                display_index,
                record.get("sample_name", ""),
                record.get("analysis_time", ""),
                self._format_float(record.get("cm_per_pixel"), 5),
                self._format_float(record.get("plant_height_cm"), 2),
                self._format_float(record.get("canopy_width_cm"), 2),
                self._format_float(record.get("projected_area_cm2"), 2),
                self._format_percent(record.get("green_coverage")),
                self._format_float(record.get("growth_score"), 2),
                record.get("note", "") or "",
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                if col_index == 0:
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setData(Qt.UserRole, record_id)

                self.table.setItem(row_index, col_index, item)

        self.detail_label.setText(
            f"当前共显示 {len(records)} 条记录。"
            "表格第一列为连续显示序号，数据库内部记录ID不作为显示序号。"
        )

    def _update_summary(self, records: list[dict]) -> None:
        if not records:
            self.summary_label.setText("当前查询结果为空，暂无统计摘要。")
            return

        height_values = self._collect_float_values(records, "plant_height_cm")
        width_values = self._collect_float_values(records, "canopy_width_cm")
        area_values = self._collect_float_values(records, "projected_area_cm2")
        coverage_values = self._collect_float_values(records, "green_coverage")
        score_values = self._collect_float_values(records, "growth_score")

        text = (
            f"当前显示记录数：{len(records)} 条\n\n"
            f"【株高】平均 {self._format_average(height_values, 2)} cm，"
            f"最小 {self._format_min(height_values, 2)} cm，"
            f"最大 {self._format_max(height_values, 2)} cm\n"
            f"【冠幅】平均 {self._format_average(width_values, 2)} cm，"
            f"最小 {self._format_min(width_values, 2)} cm，"
            f"最大 {self._format_max(width_values, 2)} cm\n"
            f"【投影面积】平均 {self._format_average(area_values, 2)} cm²，"
            f"最小 {self._format_min(area_values, 2)} cm²，"
            f"最大 {self._format_max(area_values, 2)} cm²\n"
            f"【绿色覆盖率】平均 {self._format_average_percent(coverage_values)}，"
            f"最小 {self._format_min_percent(coverage_values)}，"
            f"最大 {self._format_max_percent(coverage_values)}\n"
            f"【长势评分】平均 {self._format_average(score_values, 2)}，"
            f"最小 {self._format_min(score_values, 2)}，"
            f"最大 {self._format_max(score_values, 2)}"
        )

        self.summary_label.setText(text)

    def _update_action_buttons(self) -> None:
        has_selection = bool(self.table.selectionModel().selectedRows())
        self.btn_review.setEnabled(has_selection)

    def get_selected_record_id(self) -> int | None:
        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            return None

        row_index = selected_rows[0].row()
        item = self.table.item(row_index, 0)

        if item is None:
            return None

        record_id = item.data(Qt.UserRole)

        if record_id is None:
            return None

        try:
            return int(record_id)
        except (TypeError, ValueError):
            return None

    def get_selected_record(self) -> dict | None:
        record_id = self.get_selected_record_id()

        if record_id is None:
            return None

        return self.repository.get_record(record_id)

    def get_selected_display_index(self) -> int | None:
        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            return None

        return selected_rows[0].row() + 1

    def review_selected_record(self) -> None:
        record = self.get_selected_record()
        display_index = self.get_selected_display_index()

        if record is None or display_index is None:
            QMessageBox.information(self, "提示", "请先选择一条记录。")
            return

        dialog = RecordReviewDialog(
            display_index=display_index,
            record=record,
            parent=self,
        )
        dialog.exec()

    def update_detail(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            self.detail_label.setText("请选择一条记录查看摘要。")
            return

        row_index = selected_rows[0].row()
        display_index = row_index + 1

        record = self.get_selected_record()

        if record is None:
            self.detail_label.setText("请选择一条记录查看摘要。")
            return

        text = (
            f"显示序号：{display_index}\n"
            f"内部记录ID：{record.get('id')}\n"
            f"样本名称：{record.get('sample_name')}\n"
            f"原图路径：{record.get('image_path')}\n"
            f"掩膜路径：{record.get('mask_path')}\n"
            f"叠加图路径：{record.get('overlay_path')}\n"
            f"软件版本：{record.get('software_version')}"
        )

        self.detail_label.setText(text)

    def edit_note(self) -> None:
        record = self.get_selected_record()

        if record is None:
            QMessageBox.information(self, "提示", "请先选择一条记录。")
            return

        old_note = record.get("note", "") or ""

        new_note, ok = QInputDialog.getMultiLineText(
            self,
            "编辑备注",
            "请输入备注内容：",
            old_note,
        )

        if not ok:
            return

        success = self.repository.update_note(
            record_id=int(record["id"]),
            note=new_note,
        )

        if success:
            QMessageBox.information(self, "保存成功", "备注已更新。")
            self.refresh_records()
        else:
            QMessageBox.warning(self, "保存失败", "备注更新失败。")

    def delete_selected_record(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选择一条记录。")
            return

        row_index = selected_rows[0].row()
        display_index = row_index + 1

        record = self.get_selected_record()

        if record is None:
            QMessageBox.information(self, "提示", "请先选择一条记录。")
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            (
                f"确定要删除当前显示序号为 {display_index} 的记录吗？\n"
                f"样本名称：{record.get('sample_name')}\n\n"
                "该操作只删除数据库记录，不删除原始图像、掩膜图或叠加图文件。"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        success = self.repository.delete_record(int(record["id"]))

        if success:
            QMessageBox.information(self, "删除成功", "记录已删除，显示序号已重新排列。")
            self.refresh_records()
        else:
            QMessageBox.warning(self, "删除失败", "记录删除失败。")

    def export_excel(self) -> None:
        if not self.records:
            QMessageBox.information(self, "提示", "暂无可导出的历史记录。")
            return

        default_name = f"history_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        default_path = output_dir() / default_name

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出历史记录 Excel",
            str(default_path),
            "Excel Files (*.xlsx)",
        )

        if not file_path:
            return

        try:
            output_path = self.exporter.export_records_to_excel(
                self.records,
                Path(file_path),
            )
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", f"导出 Excel 时发生错误：\n{exc}")
            return

        QMessageBox.information(self, "导出成功", f"历史记录已导出：\n{output_path}")

    def export_csv(self) -> None:
        if not self.records:
            QMessageBox.information(self, "提示", "暂无可导出的历史记录。")
            return

        default_name = f"history_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        default_path = output_dir() / default_name

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出历史记录 CSV",
            str(default_path),
            "CSV Files (*.csv)",
        )

        if not file_path:
            return

        try:
            output_path = self.exporter.export_records_to_csv(
                self.records,
                Path(file_path),
            )
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", f"导出 CSV 时发生错误：\n{exc}")
            return

        QMessageBox.information(self, "导出成功", f"历史记录已导出：\n{output_path}")

    @staticmethod
    def _collect_float_values(records: list[dict], key: str) -> list[float]:
        values: list[float] = []

        for record in records:
            value = record.get(key)

            if value is None:
                continue

            try:
                values.append(float(value))
            except (TypeError, ValueError):
                continue

        return values

    @staticmethod
    def _format_average(values: list[float], digits: int) -> str:
        if not values:
            return "-"

        return f"{sum(values) / len(values):.{digits}f}"

    @staticmethod
    def _format_min(values: list[float], digits: int) -> str:
        if not values:
            return "-"

        return f"{min(values):.{digits}f}"

    @staticmethod
    def _format_max(values: list[float], digits: int) -> str:
        if not values:
            return "-"

        return f"{max(values):.{digits}f}"

    @staticmethod
    def _format_average_percent(values: list[float]) -> str:
        if not values:
            return "-"

        return f"{sum(values) / len(values) * 100:.2f}%"

    @staticmethod
    def _format_min_percent(values: list[float]) -> str:
        if not values:
            return "-"

        return f"{min(values) * 100:.2f}%"

    @staticmethod
    def _format_max_percent(values: list[float]) -> str:
        if not values:
            return "-"

        return f"{max(values) * 100:.2f}%"

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