# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QGridLayout,
)

from rice_phenotype import APP_NAME_CN, APP_NAME_EN, __version__


class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(22)

        title = QLabel(f"{APP_NAME_CN} V{__version__}")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        desc = QLabel(
            f"{APP_NAME_EN}\n"
            "面向水稻育秧图像分析场景，基于传统图像处理方法实现秧苗区域分割、"
            "尺度换算、表型指标量化、历史数据管理和报告导出。"
        )
        desc.setObjectName("PageDesc")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)
        card_layout.setSpacing(14)

        section_title = QLabel("软件功能边界")
        section_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #111827;")
        card_layout.addWidget(section_title)

        boundary = QLabel(
            "本软件采用传统图像处理方法，不包含深度学习模型训练、生成式人工智能服务、"
            "云端推理或外部 AI 接口调用；不实现三维重建，也不提供农学诊断结论。"
        )
        boundary.setWordWrap(True)
        boundary.setStyleSheet("font-size: 14px; color: #374151; line-height: 1.6;")
        card_layout.addWidget(boundary)

        layout.addWidget(card)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        items = [
            ("1. 单图分析", "导入图像，完成分割、比例尺换算和表型指标计算。"),
            ("2. 批量分析", "选择文件夹，对多张图像进行批量处理并导出结果。"),
            ("3. 历史记录", "保存分析结果，支持查询、查看、备注和删除。"),
            ("4. 报告导出", "生成包含原图、掩膜、叠加图和指标表的 Word 报告。"),
        ]

        for index, (name, text) in enumerate(items):
            item_card = QFrame()
            item_card.setObjectName("Card")
            item_layout = QVBoxLayout(item_card)
            item_layout.setContentsMargins(20, 18, 20, 18)
            item_layout.setSpacing(8)

            item_title = QLabel(name)
            item_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #111827;")
            item_layout.addWidget(item_title)

            item_desc = QLabel(text)
            item_desc.setWordWrap(True)
            item_desc.setStyleSheet("font-size: 13px; color: #4B5563;")
            item_layout.addWidget(item_desc)

            row = index // 2
            col = index % 2
            grid.addWidget(item_card, row, col)

        layout.addLayout(grid)
        layout.addStretch()