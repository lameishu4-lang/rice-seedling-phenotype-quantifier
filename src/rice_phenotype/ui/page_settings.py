# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(18)

        title = QLabel("参数设置")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        desc = QLabel("本页用于设置 HSV 阈值、ExG 阈值、最小连通域面积、默认比例尺和输出目录。")
        desc.setObjectName("PageDesc")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)

        placeholder = QLabel("参数设置控件将在图像分割模块完成后接入。")
        placeholder.setStyleSheet("font-size: 15px; color: #4B5563;")
        card_layout.addWidget(placeholder)

        layout.addWidget(card)
        layout.addStretch()