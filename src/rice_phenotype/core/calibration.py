# -*- coding: utf-8 -*-

"""
尺度标定模块

本模块仅负责像素尺度与实际长度之间的换算。
默认使用 cm_per_pixel，即每个像素对应的厘米数。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CalibrationResult:
    cm_per_pixel: float
    message: str


class ScaleCalibrator:
    """图像比例尺换算工具"""

    @staticmethod
    def validate_cm_per_pixel(cm_per_pixel: float) -> CalibrationResult:
        if cm_per_pixel <= 0:
            raise ValueError("比例尺必须大于 0。")

        return CalibrationResult(
            cm_per_pixel=cm_per_pixel,
            message=f"当前比例尺为 {cm_per_pixel:.6f} cm/pixel。"
        )

    @staticmethod
    def from_reference_length(
        pixel_length: float,
        real_length_cm: float,
    ) -> CalibrationResult:
        """
        根据图像中标尺像素长度和实际长度计算 cm_per_pixel。

        Parameters
        ----------
        pixel_length:
            图像中标尺线段的像素长度。
        real_length_cm:
            标尺线段对应的真实长度，单位 cm。
        """

        if pixel_length <= 0:
            raise ValueError("标尺像素长度必须大于 0。")

        if real_length_cm <= 0:
            raise ValueError("真实长度必须大于 0。")

        cm_per_pixel = real_length_cm / pixel_length

        return CalibrationResult(
            cm_per_pixel=cm_per_pixel,
            message=(
                f"根据标尺计算得到比例尺：{cm_per_pixel:.6f} cm/pixel "
                f"({real_length_cm:.2f} cm / {pixel_length:.2f} px)。"
            )
        )