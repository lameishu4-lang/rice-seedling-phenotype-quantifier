# -*- coding: utf-8 -*-

"""
Qt 图像转换工具

用于将 numpy.ndarray 图像转换为 QPixmap，供 PySide6 界面显示。
"""

import numpy as np
from PySide6.QtGui import QImage, QPixmap


def ndarray_to_qimage(image: np.ndarray) -> QImage:
    """
    将 numpy 图像转换为 QImage。

    支持：
    - 灰度图：H x W
    - RGB 图：H x W x 3

    注意：输入 RGB 图像应为 RGB 顺序，不是 OpenCV 默认 BGR 顺序。
    """

    if image is None:
        raise ValueError("输入图像为空。")

    if not isinstance(image, np.ndarray):
        raise TypeError("输入图像必须为 numpy.ndarray。")

    if image.dtype != np.uint8:
        image = image.astype(np.uint8)

    if image.ndim == 2:
        height, width = image.shape
        bytes_per_line = width

        qimage = QImage(
            image.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_Grayscale8,
        )

        return qimage.copy()

    if image.ndim == 3 and image.shape[2] == 3:
        height, width, channels = image.shape
        bytes_per_line = channels * width

        qimage = QImage(
            image.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888,
        )

        return qimage.copy()

    raise ValueError("仅支持灰度图或 RGB 三通道图像。")


def ndarray_to_pixmap(image: np.ndarray) -> QPixmap:
    qimage = ndarray_to_qimage(image)
    return QPixmap.fromImage(qimage)