# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QSizePolicy,
)

from rice_phenotype import APP_NAME_CN, __version__
from rice_phenotype.ui.page_home import HomePage
from rice_phenotype.ui.page_single_analysis import SingleAnalysisPage
from rice_phenotype.ui.page_batch_analysis import BatchAnalysisPage
from rice_phenotype.ui.page_records import RecordsPage
from rice_phenotype.ui.page_settings import SettingsPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"{APP_NAME_CN} V{__version__}")
        self.resize(1440, 900)
        self.setMinimumSize(1200, 760)

        self.nav_buttons: dict[str, QPushButton] = {}

        self._build_ui()
        self._apply_styles()
        self.switch_page("home")

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)

        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(260)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(18, 28, 18, 20)
        sidebar_layout.setSpacing(12)

        title = QLabel("稻苗表型量化软件")
        title.setObjectName("SidebarTitle")
        title.setWordWrap(True)
        sidebar_layout.addWidget(title)

        subtitle = QLabel(f"V{__version__}\n传统图像处理桌面工具")
        subtitle.setObjectName("SidebarSubtitle")
        subtitle.setWordWrap(True)
        sidebar_layout.addWidget(subtitle)

        sidebar_layout.addSpacing(18)

        self._add_nav_button(sidebar_layout, "home", "首页")
        self._add_nav_button(sidebar_layout, "single", "单图分析")
        self._add_nav_button(sidebar_layout, "batch", "批量分析")
        self._add_nav_button(sidebar_layout, "records", "历史记录")
        self._add_nav_button(sidebar_layout, "settings", "参数设置")

        sidebar_layout.addStretch()

        boundary_label = QLabel(
            "功能边界：\n"
            "不含深度学习训练\n"
            "不含生成式 AI 服务\n"
            "不含三维重建"
        )
        boundary_label.setObjectName("BoundaryLabel")
        boundary_label.setWordWrap(True)
        sidebar_layout.addWidget(boundary_label)

        self.stack = QStackedWidget()
        self.stack.setObjectName("ContentStack")
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.pages = {
            "home": HomePage(),
            "single": SingleAnalysisPage(),
            "batch": BatchAnalysisPage(),
            "records": RecordsPage(),
            "settings": SettingsPage(),
        }

        for page in self.pages.values():
            self.stack.addWidget(page)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)

    def _add_nav_button(self, layout: QVBoxLayout, key: str, text: str) -> None:
        button = QPushButton(text)
        button.setObjectName("NavButton")
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(lambda checked=False, page_key=key: self.switch_page(page_key))
        layout.addWidget(button)
        self.nav_buttons[key] = button

    def switch_page(self, key: str) -> None:
        if key not in self.pages:
            return

        self.stack.setCurrentWidget(self.pages[key])

        for page_key, button in self.nav_buttons.items():
            button.setProperty("active", page_key == key)
            button.style().unpolish(button)
            button.style().polish(button)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #F3F4F6;
            }

            QWidget#Sidebar {
                background-color: #0F172A;
            }

            QLabel#SidebarTitle {
                color: #FFFFFF;
                font-size: 22px;
                font-weight: 700;
                line-height: 1.4;
            }

            QLabel#SidebarSubtitle {
                color: #CBD5E1;
                font-size: 13px;
                line-height: 1.5;
            }

            QLabel#BoundaryLabel {
                color: #CBD5E1;
                background-color: #1E293B;
                border-radius: 10px;
                padding: 12px;
                font-size: 12px;
                line-height: 1.6;
            }

            QPushButton#NavButton {
                background-color: transparent;
                color: #CBD5E1;
                border: none;
                border-radius: 10px;
                padding: 12px 16px;
                text-align: left;
                font-size: 15px;
            }

            QPushButton#NavButton:hover {
                background-color: #1E293B;
                color: #FFFFFF;
            }

            QPushButton#NavButton[active="true"] {
                background-color: #2563EB;
                color: #FFFFFF;
                font-weight: 600;
            }

            QStackedWidget#ContentStack {
                background-color: #F3F4F6;
            }

            QLabel#PageTitle {
                color: #111827;
                font-size: 26px;
                font-weight: 700;
            }

            QLabel#PageDesc {
                color: #4B5563;
                font-size: 14px;
            }

            QWidget#Card {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 14px;
            }

            QPushButton#PrimaryButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: 600;
            }

            QPushButton#PrimaryButton:hover {
                background-color: #1D4ED8;
            }

            QPushButton#SecondaryButton {
                background-color: #E5E7EB;
                color: #111827;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
            }

            QPushButton#SecondaryButton:hover {
                background-color: #D1D5DB;
            }
            """
        )