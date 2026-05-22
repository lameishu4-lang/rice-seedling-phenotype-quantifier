# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QMessageBox,
    QGridLayout,
)

from rice_phenotype.core.settings import AppSettings, SettingsManager


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.manager = SettingsManager()
        self.settings = self.manager.load()

        self._build_ui()
        self._load_to_widgets()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(18)

        title = QLabel("参数设置")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        desc = QLabel(
            "本页用于设置绿色区域分割参数、形态学处理参数和默认比例尺。"
            "参数保存后会被单图分析和批量分析读取。"
        )
        desc.setObjectName("PageDesc")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)
        card_layout.setSpacing(18)

        section_title = QLabel("图像分割参数")
        section_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #111827;")
        card_layout.addWidget(section_title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)

        self.method_combo = QComboBox()
        self.method_combo.addItems(["HSV", "ExG", "HSV+ExG"])

        self.h_min = self._create_spinbox(0, 179)
        self.s_min = self._create_spinbox(0, 255)
        self.v_min = self._create_spinbox(0, 255)

        self.h_max = self._create_spinbox(0, 179)
        self.s_max = self._create_spinbox(0, 255)
        self.v_max = self._create_spinbox(0, 255)

        self.exg_threshold = self._create_spinbox(0, 255)
        self.min_area = self._create_spinbox(1, 999999)
        self.kernel_size = self._create_spinbox(1, 99)

        self.default_scale = QDoubleSpinBox()
        self.default_scale.setDecimals(5)
        self.default_scale.setMinimum(0.00001)
        self.default_scale.setMaximum(10.0)
        self.default_scale.setSingleStep(0.001)
        self.default_scale.setSuffix(" cm/pixel")

        row = 0
        grid.addWidget(QLabel("分割方法："), row, 0)
        grid.addWidget(self.method_combo, row, 1)

        row += 1
        grid.addWidget(QLabel("HSV H 下限："), row, 0)
        grid.addWidget(self.h_min, row, 1)
        grid.addWidget(QLabel("HSV H 上限："), row, 2)
        grid.addWidget(self.h_max, row, 3)

        row += 1
        grid.addWidget(QLabel("HSV S 下限："), row, 0)
        grid.addWidget(self.s_min, row, 1)
        grid.addWidget(QLabel("HSV S 上限："), row, 2)
        grid.addWidget(self.s_max, row, 3)

        row += 1
        grid.addWidget(QLabel("HSV V 下限："), row, 0)
        grid.addWidget(self.v_min, row, 1)
        grid.addWidget(QLabel("HSV V 上限："), row, 2)
        grid.addWidget(self.v_max, row, 3)

        row += 1
        grid.addWidget(QLabel("ExG 阈值："), row, 0)
        grid.addWidget(self.exg_threshold, row, 1)
        grid.addWidget(QLabel("最小连通域面积："), row, 2)
        grid.addWidget(self.min_area, row, 3)

        row += 1
        grid.addWidget(QLabel("形态学核大小："), row, 0)
        grid.addWidget(self.kernel_size, row, 1)
        grid.addWidget(QLabel("默认比例尺："), row, 2)
        grid.addWidget(self.default_scale, row, 3)

        card_layout.addLayout(grid)

        note = QLabel(
            "说明：HSV 参数用于绿色区域提取；ExG 阈值用于绿色增强分割；"
            "最小连通域面积用于过滤小噪声区域；默认比例尺用于像素到厘米的换算。"
        )
        note.setWordWrap(True)
        note.setStyleSheet("font-size: 13px; color: #4B5563;")
        card_layout.addWidget(note)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.btn_save = QPushButton("保存参数")
        self.btn_save.setObjectName("PrimaryButton")
        self.btn_save.clicked.connect(self.save_settings)

        self.btn_reset = QPushButton("恢复默认")
        self.btn_reset.setObjectName("SecondaryButton")
        self.btn_reset.clicked.connect(self.reset_settings)

        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_reset)

        card_layout.addLayout(button_layout)

        layout.addWidget(card)
        layout.addStretch()

    @staticmethod
    def _create_spinbox(min_value: int, max_value: int) -> QSpinBox:
        box = QSpinBox()
        box.setMinimum(min_value)
        box.setMaximum(max_value)
        box.setSingleStep(1)
        return box

    def _load_to_widgets(self) -> None:
        self.method_combo.setCurrentText(self.settings.segmentation_method)

        self.h_min.setValue(self.settings.hsv_h_min)
        self.s_min.setValue(self.settings.hsv_s_min)
        self.v_min.setValue(self.settings.hsv_v_min)

        self.h_max.setValue(self.settings.hsv_h_max)
        self.s_max.setValue(self.settings.hsv_s_max)
        self.v_max.setValue(self.settings.hsv_v_max)

        self.exg_threshold.setValue(self.settings.exg_threshold)
        self.min_area.setValue(self.settings.min_area)
        self.kernel_size.setValue(self.settings.kernel_size)

        self.default_scale.setValue(self.settings.default_cm_per_pixel)

    def _read_from_widgets(self) -> AppSettings:
        kernel_size = int(self.kernel_size.value())

        if kernel_size % 2 == 0:
            kernel_size += 1

        return AppSettings(
            segmentation_method=self.method_combo.currentText(),
            hsv_h_min=int(self.h_min.value()),
            hsv_s_min=int(self.s_min.value()),
            hsv_v_min=int(self.v_min.value()),
            hsv_h_max=int(self.h_max.value()),
            hsv_s_max=int(self.s_max.value()),
            hsv_v_max=int(self.v_max.value()),
            exg_threshold=int(self.exg_threshold.value()),
            min_area=int(self.min_area.value()),
            kernel_size=kernel_size,
            default_cm_per_pixel=float(self.default_scale.value()),
        )

    def save_settings(self) -> None:
        settings = self._read_from_widgets()

        if settings.hsv_h_min > settings.hsv_h_max:
            QMessageBox.warning(self, "参数错误", "HSV H 下限不能大于上限。")
            return

        if settings.hsv_s_min > settings.hsv_s_max:
            QMessageBox.warning(self, "参数错误", "HSV S 下限不能大于上限。")
            return

        if settings.hsv_v_min > settings.hsv_v_max:
            QMessageBox.warning(self, "参数错误", "HSV V 下限不能大于上限。")
            return

        self.manager.save(settings)
        self.settings = settings

        QMessageBox.information(self, "保存成功", "参数已保存，后续分析将读取当前设置。")

    def reset_settings(self) -> None:
        reply = QMessageBox.question(
            self,
            "确认恢复默认",
            "确定要恢复默认参数吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        self.settings = self.manager.reset()
        self._load_to_widgets()

        QMessageBox.information(self, "已恢复", "参数已恢复为默认值。")