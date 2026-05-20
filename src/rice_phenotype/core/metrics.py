# -*- coding: utf-8 -*-

"""
表型指标计算模块

本模块基于二维图像分割结果计算水稻秧苗图像表型指标。
所有指标均来源于图像掩膜和比例尺换算，不包含 AI 预测或农学诊断。
"""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class PhenotypeMetrics:
    plant_height_px: float
    plant_height_cm: float
    canopy_width_px: float
    canopy_width_cm: float
    projected_area_px: float
    projected_area_cm2: float
    green_coverage: float
    exg_mean: float
    green_ratio: float
    bbox_fill_ratio: float
    growth_score: float


class PhenotypeCalculator:
    """水稻秧苗二维图像表型指标计算器"""

    def calculate(
        self,
        image_rgb: np.ndarray,
        mask: np.ndarray,
        cm_per_pixel: float,
        valid_area_px: int | None = None,
    ) -> PhenotypeMetrics:
        self._validate_inputs(image_rgb, mask, cm_per_pixel)

        if valid_area_px is None or valid_area_px <= 0:
            height, width = mask.shape[:2]
            valid_area_px = int(height * width)

        mask_bool = mask > 0
        projected_area_px = float(np.count_nonzero(mask_bool))

        if projected_area_px <= 0:
            raise ValueError("掩膜中未检测到有效秧苗区域，无法计算表型指标。")

        x, y, w, h = self._compute_bbox(mask)

        plant_height_px = float(h)
        canopy_width_px = float(w)

        plant_height_cm = plant_height_px * cm_per_pixel
        canopy_width_cm = canopy_width_px * cm_per_pixel
        projected_area_cm2 = projected_area_px * (cm_per_pixel ** 2)

        green_coverage = projected_area_px / max(float(valid_area_px), 1.0)

        exg_mean = self._compute_exg_mean(image_rgb, mask_bool)
        green_ratio = self._compute_green_ratio(image_rgb, mask_bool)

        bbox_area = max(float(w * h), 1.0)
        bbox_fill_ratio = projected_area_px / bbox_area

        growth_score = self._compute_growth_score(
            green_coverage=green_coverage,
            green_ratio=green_ratio,
            bbox_fill_ratio=bbox_fill_ratio,
        )

        return PhenotypeMetrics(
            plant_height_px=plant_height_px,
            plant_height_cm=plant_height_cm,
            canopy_width_px=canopy_width_px,
            canopy_width_cm=canopy_width_cm,
            projected_area_px=projected_area_px,
            projected_area_cm2=projected_area_cm2,
            green_coverage=green_coverage,
            exg_mean=exg_mean,
            green_ratio=green_ratio,
            bbox_fill_ratio=bbox_fill_ratio,
            growth_score=growth_score,
        )

    @staticmethod
    def _validate_inputs(
        image_rgb: np.ndarray,
        mask: np.ndarray,
        cm_per_pixel: float,
    ) -> None:
        if image_rgb is None:
            raise ValueError("输入图像为空。")

        if mask is None:
            raise ValueError("输入掩膜为空。")

        if not isinstance(image_rgb, np.ndarray):
            raise TypeError("输入图像必须为 numpy.ndarray。")

        if not isinstance(mask, np.ndarray):
            raise TypeError("输入掩膜必须为 numpy.ndarray。")

        if image_rgb.ndim != 3 or image_rgb.shape[2] != 3:
            raise ValueError("输入图像必须为 RGB 三通道图像。")

        if mask.ndim != 2:
            raise ValueError("掩膜必须为单通道二值图像。")

        if image_rgb.shape[:2] != mask.shape[:2]:
            raise ValueError("图像尺寸与掩膜尺寸不一致。")

        if cm_per_pixel <= 0:
            raise ValueError("比例尺 cm_per_pixel 必须大于 0。")

    @staticmethod
    def _compute_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
        coords = cv2.findNonZero(mask)

        if coords is None:
            return 0, 0, 0, 0

        x, y, w, h = cv2.boundingRect(coords)
        return int(x), int(y), int(w), int(h)

    @staticmethod
    def _compute_exg_mean(image_rgb: np.ndarray, mask_bool: np.ndarray) -> float:
        image_float = image_rgb.astype(np.float32)

        r = image_float[:, :, 0]
        g = image_float[:, :, 1]
        b = image_float[:, :, 2]

        exg = 2 * g - r - b

        return float(np.mean(exg[mask_bool]))

    @staticmethod
    def _compute_green_ratio(image_rgb: np.ndarray, mask_bool: np.ndarray) -> float:
        image_float = image_rgb.astype(np.float32)

        r = image_float[:, :, 0]
        g = image_float[:, :, 1]
        b = image_float[:, :, 2]

        denominator = r + g + b + 1e-6
        green_ratio_image = g / denominator

        return float(np.mean(green_ratio_image[mask_bool]))

    @staticmethod
    def _compute_growth_score(
        green_coverage: float,
        green_ratio: float,
        bbox_fill_ratio: float,
    ) -> float:
        """
        计算软件内部长势评分。

        注意：该评分仅用于同批次样本之间的相对比较，
        不作为农学诊断、生产决策或病害判断依据。
        """

        coverage_score = min(max(green_coverage / 0.75, 0.0), 1.0)

        # 普通 RGB 图像中，绿色比例通常在 0-1 之间。
        # 这里将 0.25-0.50 映射到 0-1，作为相对叶色得分。
        color_score = min(max((green_ratio - 0.25) / 0.25, 0.0), 1.0)

        # 掩膜在外接矩形中的填充程度，反映二维投影密集程度。
        density_score = min(max(bbox_fill_ratio / 0.65, 0.0), 1.0)

        score = 100.0 * (
            0.40 * coverage_score
            + 0.40 * color_score
            + 0.20 * density_score
        )

        return float(round(score, 2))