# -*- coding: utf-8 -*-

"""
批量图像分析模块

本模块用于对文件夹中的多张图像逐张执行：
1. 图像读取；
2. 绿色区域分割；
3. 比例尺换算；
4. 二维表型指标计算；
5. 批量结果封装。

说明：
BatchItemResult 中保留 mask 和 overlay，
用于批量样本复核弹窗显示分割掩膜和叠加结果，
也用于批量成功记录保存时写出图像文件。
"""

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from rice_phenotype.core.calibration import ScaleCalibrator
from rice_phenotype.core.metrics import PhenotypeCalculator, PhenotypeMetrics
from rice_phenotype.core.segmentation import (
    SeedlingSegmenter,
    SegmentationConfig,
)


@dataclass
class BatchItemResult:
    """单张批量分析结果"""

    image_path: Path
    sample_name: str
    success: bool
    message: str
    image_width: int = 0
    image_height: int = 0
    metrics: PhenotypeMetrics | None = None
    mask: np.ndarray | None = None
    overlay: np.ndarray | None = None


class BatchAnalyzer:
    """批量图像分析器"""

    SUPPORTED_SUFFIXES = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
    }

    def __init__(self):
        self.segmenter = SeedlingSegmenter()
        self.calibrator = ScaleCalibrator()
        self.calculator = PhenotypeCalculator()

    def list_images(self, folder: Path) -> list[Path]:
        """列出文件夹中的支持格式图像"""

        folder = Path(folder)

        if not folder.exists():
            raise FileNotFoundError(f"文件夹不存在：{folder}")

        if not folder.is_dir():
            raise NotADirectoryError(f"当前路径不是文件夹：{folder}")

        image_paths: list[Path] = []

        for path in folder.iterdir():
            if not path.is_file():
                continue

            if path.suffix.lower() in self.SUPPORTED_SUFFIXES:
                image_paths.append(path)

        image_paths.sort(key=lambda item: item.name.lower())

        return image_paths

    def analyze_single_image(
        self,
        image_path: Path,
        cm_per_pixel: float,
        config: SegmentationConfig,
    ) -> BatchItemResult:
        """分析单张图像"""

        image_path = Path(image_path)

        try:
            image_rgb = self._read_image_rgb(image_path)

            if image_rgb is None:
                return BatchItemResult(
                    image_path=image_path,
                    sample_name=image_path.name,
                    success=False,
                    message="图像读取失败",
                )

            image_height, image_width = image_rgb.shape[:2]

            self.calibrator.validate_cm_per_pixel(cm_per_pixel)

            # 这里使用位置参数，保持与单图分析页调用方式一致。
            segmentation = self.segmenter.segment(image_rgb, config)

            if not segmentation.success:
                return BatchItemResult(
                    image_path=image_path,
                    sample_name=image_path.name,
                    success=False,
                    message=segmentation.message,
                    image_width=image_width,
                    image_height=image_height,
                    mask=getattr(segmentation, "mask", None),
                    overlay=getattr(segmentation, "overlay", None),
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
                image_width=image_width,
                image_height=image_height,
                metrics=metrics,
                mask=segmentation.mask,
                overlay=segmentation.overlay,
            )

        except Exception as exc:
            return BatchItemResult(
                image_path=image_path,
                sample_name=image_path.name,
                success=False,
                message=f"分析异常：{exc}",
            )

    @staticmethod
    def _read_image_rgb(image_path: Path) -> np.ndarray | None:
        """兼容中文路径的图像读取"""

        image_bgr = cv2.imdecode(
            np.fromfile(str(image_path), dtype=np.uint8),
            cv2.IMREAD_COLOR,
        )

        if image_bgr is None:
            return None

        return cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)