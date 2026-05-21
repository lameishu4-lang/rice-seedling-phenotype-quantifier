# -*- coding: utf-8 -*-

"""
批量图像分析模块

本模块负责批量读取文件夹中的图像，并基于传统图像处理流程完成：
图像读取、绿色区域分割、比例尺换算和二维表型指标计算。
"""

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from rice_phenotype.core.segmentation import (
    SeedlingSegmenter,
    SegmentationConfig,
)
from rice_phenotype.core.metrics import (
    PhenotypeCalculator,
    PhenotypeMetrics,
)


SUPPORTED_IMAGE_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
}


@dataclass
class BatchItemResult:
    image_path: Path
    sample_name: str
    success: bool
    message: str
    image_width: int | None = None
    image_height: int | None = None
    plant_area_px: int | None = None
    bbox: tuple[int, int, int, int] | None = None
    metrics: PhenotypeMetrics | None = None


class BatchAnalyzer:
    """水稻秧苗图像批量分析器"""

    def __init__(self):
        self.segmenter = SeedlingSegmenter()
        self.calculator = PhenotypeCalculator()

    def list_images(self, folder_path: Path) -> list[Path]:
        if not folder_path.exists():
            raise FileNotFoundError(f"文件夹不存在：{folder_path}")

        if not folder_path.is_dir():
            raise NotADirectoryError(f"路径不是文件夹：{folder_path}")

        image_paths: list[Path] = []

        for path in folder_path.iterdir():
            if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES:
                image_paths.append(path)

        image_paths.sort(key=lambda p: p.name.lower())

        return image_paths

    def analyze_folder(
        self,
        folder_path: Path,
        cm_per_pixel: float,
        config: SegmentationConfig | None = None,
    ) -> list[BatchItemResult]:
        if cm_per_pixel <= 0:
            raise ValueError("比例尺 cm_per_pixel 必须大于 0。")

        if config is None:
            config = SegmentationConfig()

        image_paths = self.list_images(folder_path)

        results: list[BatchItemResult] = []

        for image_path in image_paths:
            result = self.analyze_single_image(
                image_path=image_path,
                cm_per_pixel=cm_per_pixel,
                config=config,
            )
            results.append(result)

        return results

    def analyze_single_image(
        self,
        image_path: Path,
        cm_per_pixel: float,
        config: SegmentationConfig,
    ) -> BatchItemResult:
        try:
            image_rgb = self._read_image_rgb(image_path)

            height, width = image_rgb.shape[:2]

            segmentation = self.segmenter.segment(
                image_rgb=image_rgb,
                config=config,
            )

            if not segmentation.success:
                return BatchItemResult(
                    image_path=image_path,
                    sample_name=image_path.name,
                    success=False,
                    message=segmentation.message,
                    image_width=width,
                    image_height=height,
                    plant_area_px=0,
                    bbox=segmentation.bbox,
                    metrics=None,
                )

            metrics = self.calculator.calculate(
                image_rgb=image_rgb,
                mask=segmentation.mask,
                cm_per_pixel=cm_per_pixel,
                valid_area_px=segmentation.valid_area_px,
            )

            return BatchItemResult(
                image_path=image_path,
                sample_name=image_path.name,
                success=True,
                message="分析成功",
                image_width=width,
                image_height=height,
                plant_area_px=segmentation.plant_area_px,
                bbox=segmentation.bbox,
                metrics=metrics,
            )

        except Exception as exc:
            return BatchItemResult(
                image_path=image_path,
                sample_name=image_path.name,
                success=False,
                message=str(exc),
                image_width=None,
                image_height=None,
                plant_area_px=None,
                bbox=None,
                metrics=None,
            )

    @staticmethod
    def _read_image_rgb(image_path: Path) -> np.ndarray:
        image_bgr = cv2.imdecode(
            np.fromfile(str(image_path), dtype=np.uint8),
            cv2.IMREAD_COLOR,
        )

        if image_bgr is None:
            raise ValueError("图像读取失败，请检查文件格式或路径。")

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        return image_rgb