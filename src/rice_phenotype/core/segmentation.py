# -*- coding: utf-8 -*-

"""
图像分割模块

本模块仅使用传统图像处理方法，包括 HSV 阈值分割、ExG 绿色增强、
形态学处理和连通域过滤，不包含深度学习模型或生成式 AI。
"""

from dataclasses import dataclass
from typing import Literal

import cv2
import numpy as np


SegmentationMethod = Literal["HSV", "ExG", "HSV+ExG"]


@dataclass
class SegmentationConfig:
    """秧苗区域分割参数"""

    hsv_lower: tuple[int, int, int] = (35, 40, 40)
    hsv_upper: tuple[int, int, int] = (85, 255, 255)
    exg_threshold: int = 30
    min_area: int = 300
    kernel_size: int = 5
    method: SegmentationMethod = "HSV"


@dataclass
class SegmentationResult:
    """秧苗区域分割结果"""

    success: bool
    mask: np.ndarray
    overlay: np.ndarray
    bbox: tuple[int, int, int, int]
    valid_area_px: int
    plant_area_px: int
    message: str


class SeedlingSegmenter:
    """水稻秧苗绿色区域分割器"""

    def segment(
        self,
        image_rgb: np.ndarray,
        config: SegmentationConfig | None = None,
    ) -> SegmentationResult:
        """
        对输入 RGB 图像进行秧苗区域分割。

        Parameters
        ----------
        image_rgb:
            RGB 格式图像，shape 为 H x W x 3。
        config:
            分割配置。

        Returns
        -------
        SegmentationResult
            分割结果。
        """

        if config is None:
            config = SegmentationConfig()

        self._validate_image(image_rgb)

        height, width = image_rgb.shape[:2]
        valid_area_px = int(height * width)

        hsv_mask = self._segment_by_hsv(image_rgb, config)
        exg_mask = self._segment_by_exg(image_rgb, config)

        if config.method == "HSV":
            raw_mask = hsv_mask
        elif config.method == "ExG":
            raw_mask = exg_mask
        elif config.method == "HSV+ExG":
            raw_mask = cv2.bitwise_and(hsv_mask, exg_mask)
        else:
            raise ValueError(f"不支持的分割方法：{config.method}")

        processed_mask = self._post_process_mask(raw_mask, config)

        plant_area_px = int(np.count_nonzero(processed_mask))

        if plant_area_px == 0:
            empty_overlay = image_rgb.copy()
            return SegmentationResult(
                success=False,
                mask=processed_mask,
                overlay=empty_overlay,
                bbox=(0, 0, 0, 0),
                valid_area_px=valid_area_px,
                plant_area_px=0,
                message="未检测到有效绿色秧苗区域，请调整阈值或检查图像。"
            )

        bbox = self._compute_bbox(processed_mask)
        overlay = self._create_overlay(image_rgb, processed_mask)

        return SegmentationResult(
            success=True,
            mask=processed_mask,
            overlay=overlay,
            bbox=bbox,
            valid_area_px=valid_area_px,
            plant_area_px=plant_area_px,
            message="分割完成。"
        )

    @staticmethod
    def _validate_image(image_rgb: np.ndarray) -> None:
        if image_rgb is None:
            raise ValueError("输入图像为空。")

        if not isinstance(image_rgb, np.ndarray):
            raise TypeError("输入图像必须为 numpy.ndarray。")

        if image_rgb.ndim != 3 or image_rgb.shape[2] != 3:
            raise ValueError("输入图像必须为 RGB 三通道图像。")

        if image_rgb.dtype != np.uint8:
            raise ValueError("输入图像数据类型必须为 uint8。")

    @staticmethod
    def _segment_by_hsv(image_rgb: np.ndarray, config: SegmentationConfig) -> np.ndarray:
        hsv_image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)

        lower = np.array(config.hsv_lower, dtype=np.uint8)
        upper = np.array(config.hsv_upper, dtype=np.uint8)

        mask = cv2.inRange(hsv_image, lower, upper)
        return mask

    @staticmethod
    def _segment_by_exg(image_rgb: np.ndarray, config: SegmentationConfig) -> np.ndarray:
        image_float = image_rgb.astype(np.float32)

        r = image_float[:, :, 0]
        g = image_float[:, :, 1]
        b = image_float[:, :, 2]

        exg = 2 * g - r - b

        exg_min = float(np.min(exg))
        exg_max = float(np.max(exg))

        if exg_max - exg_min < 1e-6:
            exg_norm = np.zeros_like(exg, dtype=np.uint8)
        else:
            exg_norm = ((exg - exg_min) / (exg_max - exg_min) * 255).astype(np.uint8)

        _, mask = cv2.threshold(
            exg_norm,
            config.exg_threshold,
            255,
            cv2.THRESH_BINARY,
        )

        return mask

    @staticmethod
    def _post_process_mask(mask: np.ndarray, config: SegmentationConfig) -> np.ndarray:
        kernel_size = max(int(config.kernel_size), 1)

        if kernel_size % 2 == 0:
            kernel_size += 1

        kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)

        cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)

        filtered = SeedlingSegmenter._filter_small_components(
            cleaned,
            min_area=max(int(config.min_area), 1),
        )

        return filtered

    @staticmethod
    def _filter_small_components(mask: np.ndarray, min_area: int) -> np.ndarray:
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            mask,
            connectivity=8,
        )

        output = np.zeros_like(mask, dtype=np.uint8)

        for label_index in range(1, num_labels):
            area = stats[label_index, cv2.CC_STAT_AREA]

            if area >= min_area:
                output[labels == label_index] = 255

        return output

    @staticmethod
    def _compute_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
        coords = cv2.findNonZero(mask)

        if coords is None:
            return 0, 0, 0, 0

        x, y, w, h = cv2.boundingRect(coords)
        return int(x), int(y), int(w), int(h)

    @staticmethod
    def _create_overlay(image_rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
        overlay = image_rgb.copy()

        green_layer = np.zeros_like(image_rgb, dtype=np.uint8)
        green_layer[:, :, 1] = 255

        mask_bool = mask > 0

        overlay[mask_bool] = cv2.addWeighted(
            image_rgb[mask_bool],
            0.65,
            green_layer[mask_bool],
            0.35,
            0,
        )

        return overlay