# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame


class RecordsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(18)

        title = QLabel("历史记录")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        desc = QLabel("本页用于查看、查询、备注、删除和导出历史分析记录。")
        desc.setObjectName("PageDesc")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)

        placeholder = QLabel("历史记录功能将在 SQLite 数据库模块完成后接入。")
        placeholder.setStyleSheet("font-size: 15px; color: #4B5563;")
        card_layout.addWidget(placeholder)

        layout.addWidget(card)
        layout.addStretch()