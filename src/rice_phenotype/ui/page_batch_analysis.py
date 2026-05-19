# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame


class BatchAnalysisPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(18)

        title = QLabel("批量分析")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        desc = QLabel("本页用于文件夹图像批量处理、进度展示、失败记录和 Excel/CSV 导出。")
        desc.setObjectName("PageDesc")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)

        placeholder = QLabel("批量分析功能将在后续开发中实现。")
        placeholder.setStyleSheet("font-size: 15px; color: #4B5563;")
        card_layout.addWidget(placeholder)

        layout.addWidget(card)
        layout.addStretch()