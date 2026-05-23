# -*- coding: utf-8 -*-

"""
批量表型统计模块

本模块用于对批量分析结果进行统计汇总，包括成功数量、失败数量、
成功率以及主要表型指标的均值、最小值和最大值。
"""

from dataclasses import dataclass
from statistics import mean
from typing import Iterable

from rice_phenotype.core.batch import BatchItemResult


@dataclass
class MetricStats:
    mean_value: float | None = None
    min_value: float | None = None
    max_value: float | None = None


@dataclass
class BatchSummary:
    total_count: int
    success_count: int
    failed_count: int
    success_rate: float

    plant_height_cm: MetricStats
    canopy_width_cm: MetricStats
    projected_area_cm2: MetricStats
    green_coverage: MetricStats
    growth_score: MetricStats


class BatchStatisticsCalculator:
    """批量分析结果统计计算器"""

    @staticmethod
    def calculate(results: list[BatchItemResult]) -> BatchSummary:
        total_count = len(results)
        success_items = [
            item for item in results
            if item.success and item.metrics is not None
        ]

        success_count = len(success_items)
        failed_count = total_count - success_count

        if total_count > 0:
            success_rate = success_count / total_count
        else:
            success_rate = 0.0

        return BatchSummary(
            total_count=total_count,
            success_count=success_count,
            failed_count=failed_count,
            success_rate=success_rate,
            plant_height_cm=BatchStatisticsCalculator._metric_stats(
                item.metrics.plant_height_cm for item in success_items
            ),
            canopy_width_cm=BatchStatisticsCalculator._metric_stats(
                item.metrics.canopy_width_cm for item in success_items
            ),
            projected_area_cm2=BatchStatisticsCalculator._metric_stats(
                item.metrics.projected_area_cm2 for item in success_items
            ),
            green_coverage=BatchStatisticsCalculator._metric_stats(
                item.metrics.green_coverage for item in success_items
            ),
            growth_score=BatchStatisticsCalculator._metric_stats(
                item.metrics.growth_score for item in success_items
            ),
        )

    @staticmethod
    def _metric_stats(values: Iterable[float]) -> MetricStats:
        valid_values = [
            float(value) for value in values
            if value is not None
        ]

        if not valid_values:
            return MetricStats()

        return MetricStats(
            mean_value=mean(valid_values),
            min_value=min(valid_values),
            max_value=max(valid_values),
        )