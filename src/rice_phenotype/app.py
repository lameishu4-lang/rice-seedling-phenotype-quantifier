# -*- coding: utf-8 -*-

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from rice_phenotype.ui.main_window import MainWindow


def run_app() -> None:
    app = QApplication(sys.argv)

    app.setApplicationName("Rice Seedling Phenotype Quantifier")
    app.setOrganizationName("Rice Phenotype Quantifier Team")

    font = QFont("Microsoft YaHei")
    font.setPointSize(10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())