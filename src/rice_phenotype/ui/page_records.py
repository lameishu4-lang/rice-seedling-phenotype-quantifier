# -*- coding: utf-8 -*-

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
)

from rice_phenotype.storage.database import RecordRepository


class RecordsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.repository = RecordRepository()
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

        desc = QLabel("本页用于查看、查询、备注、删除和管理历史分析记录。")
        desc.setObjectName("PageDesc")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        toolbar_card = QFrame()
        toolbar_card.setObjectName("Card")
        toolbar_layout = QHBoxLayout(toolbar_card)
        toolbar_layout.setContentsMargins(18, 12, 18, 12)
        toolbar_layout.setSpacing(12)

        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入样本名称关键词")
        self.keyword_input.setFixedWidth(260)

        self.btn_search = QPushButton("查询")
        self.btn_search.setObjectName("PrimaryButton")
        self.btn_search.clicked.connect(self.refresh_records)

        self.btn_reset = QPushButton("重置")
        self.btn_reset.setObjectName("SecondaryButton")
        self.btn_reset.clicked.connect(self.reset_search)

        self.btn_note = QPushButton("编辑备注")
        self.btn_note.setObjectName("SecondaryButton")
        self.btn_note.clicked.connect(self.edit_note)

        self.btn_delete = QPushButton("删除记录")
        self.btn_delete.setObjectName("SecondaryButton")
        self.btn_delete.clicked.connect(self.delete_selected_record)

        toolbar_layout.addWidget(QLabel("样本查询："))
        toolbar_layout.addWidget(self.keyword_input)
        toolbar_layout.addWidget(self.btn_search)
        toolbar_layout.addWidget(self.btn_reset)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_note)
        toolbar_layout.addWidget(self.btn_delete)

        layout.addWidget(toolbar_card)

        table_card = QFrame()
        table_card.setObjectName("Card")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(18, 16, 18, 18)
        table_layout.setSpacing(12)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
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

        table_layout.addWidget(self.table)

        self.detail_label = QLabel("请选择一条记录查看摘要。")
        self.detail_label.setWordWrap(True)
        self.detail_label.setStyleSheet("font-size: 13px; color: #4B5563;")
        table_layout.addWidget(self.detail_label)

        self.table.itemSelectionChanged.connect(self.update_detail)

        layout.addWidget(table_card, stretch=1)

    def refresh_records(self) -> None:
        keyword = self.keyword_input.text().strip()
        self.records = self.repository.query_records(keyword=keyword)
        self._fill_table(self.records)

    def reset_search(self) -> None:
        self.keyword_input.clear()
        self.refresh_records()

    def _fill_table(self, records: list[dict]) -> None:
        self.table.setRowCount(len(records))

        for row_index, record in enumerate(records):
            values = [
                record.get("id", ""),
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

                self.table.setItem(row_index, col_index, item)

        self.detail_label.setText(f"当前共显示 {len(records)} 条记录。")

    def get_selected_record_id(self) -> int | None:
        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            return None

        row_index = selected_rows[0].row()
        item = self.table.item(row_index, 0)

        if item is None:
            return None

        try:
            return int(item.text())
        except ValueError:
            return None

    def get_selected_record(self) -> dict | None:
        record_id = self.get_selected_record_id()

        if record_id is None:
            return None

        return self.repository.get_record(record_id)

    def update_detail(self) -> None:
        record = self.get_selected_record()

        if record is None:
            self.detail_label.setText("请选择一条记录查看摘要。")
            return

        text = (
            f"记录编号：{record.get('id')}\n"
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
        record = self.get_selected_record()

        if record is None:
            QMessageBox.information(self, "提示", "请先选择一条记录。")
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除记录 {record.get('id')} 吗？\n该操作只删除数据库记录，不删除原始图像文件。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        success = self.repository.delete_record(int(record["id"]))

        if success:
            QMessageBox.information(self, "删除成功", "记录已删除。")
            self.refresh_records()
        else:
            QMessageBox.warning(self, "删除失败", "记录删除失败。")

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