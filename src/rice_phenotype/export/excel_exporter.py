# -*- coding: utf-8 -*-

"""
Excel / CSV 导出模块

本模块负责将批量分析结果或历史记录导出为 Excel / CSV 文件。

Excel 导出包含两个工作表：
1. 明细数据
2. 统计摘要

CSV 导出保持为明细数据，便于兼容普通表格工具。
"""

from pathlib import Path
from typing import Any

import pandas as pd

from rice_phenotype.core.batch import BatchItemResult
from rice_phenotype.core.statistics import BatchStatisticsCalculator


class ResultExporter:
    """分析结果导出工具"""

    @staticmethod
    def export_batch_results_to_excel(
        results: list[BatchItemResult],
        output_path: Path,
    ) -> Path:
        detail_rows = ResultExporter._batch_results_to_rows(results)
        summary_rows = ResultExporter._batch_summary_to_rows(results)

        df_detail = pd.DataFrame(detail_rows)
        df_summary = pd.DataFrame(summary_rows)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df_detail.to_excel(writer, sheet_name="明细数据", index=False)
            df_summary.to_excel(writer, sheet_name="统计摘要", index=False)

        return output_path

    @staticmethod
    def export_batch_results_to_csv(
        results: list[BatchItemResult],
        output_path: Path,
    ) -> Path:
        rows = ResultExporter._batch_results_to_rows(results)
        df = pd.DataFrame(rows)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        return output_path

    @staticmethod
    def export_records_to_excel(
        records: list[dict[str, Any]],
        output_path: Path,
    ) -> Path:
        detail_rows = ResultExporter._records_to_rows(records)
        summary_rows = ResultExporter._record_summary_to_rows(records)

        df_detail = pd.DataFrame(detail_rows)
        df_summary = pd.DataFrame(summary_rows)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df_detail.to_excel(writer, sheet_name="明细数据", index=False)
            df_summary.to_excel(writer, sheet_name="统计摘要", index=False)

        return output_path

    @staticmethod
    def export_records_to_csv(
        records: list[dict[str, Any]],
        output_path: Path,
    ) -> Path:
        rows = ResultExporter._records_to_rows(records)
        df = pd.DataFrame(rows)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        return output_path

    @staticmethod
    def _batch_results_to_rows(results: list[BatchItemResult]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []

        for index, item in enumerate(results, start=1):
            metrics = item.metrics

            valid_area_px = getattr(item, "valid_area_px", "")
            plant_area_px = getattr(item, "plant_area_px", "")
            bbox = getattr(item, "bbox", "")

            row = {
                "序号": index,
                "样本名称": item.sample_name,
                "图像路径": str(item.image_path),
                "分析状态": "成功" if item.success else "失败",
                "信息": item.message,
                "图像宽度(px)": item.image_width,
                "图像高度(px)": item.image_height,
                "有效图像面积(px)": valid_area_px,
                "秧苗掩膜面积(px)": plant_area_px,
                "外接矩形": str(bbox) if bbox else "",
                "株高估算(px)": metrics.plant_height_px if metrics else "",
                "株高估算(cm)": metrics.plant_height_cm if metrics else "",
                "冠幅估算(px)": metrics.canopy_width_px if metrics else "",
                "冠幅估算(cm)": metrics.canopy_width_cm if metrics else "",
                "投影面积(px)": metrics.projected_area_px if metrics else "",
                "投影面积(cm²)": metrics.projected_area_cm2 if metrics else "",
                "绿色覆盖率": metrics.green_coverage if metrics else "",
                "ExG叶色指数均值": metrics.exg_mean if metrics else "",
                "Green Ratio": metrics.green_ratio if metrics else "",
                "外接矩形填充率": metrics.bbox_fill_ratio if metrics else "",
                "长势评分": metrics.growth_score if metrics else "",
            }

            rows.append(row)

        return rows

    @staticmethod
    def _records_to_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []

        for index, record in enumerate(records, start=1):
            row = ResultExporter._record_to_row(record, display_index=index)
            rows.append(row)

        return rows

    @staticmethod
    def _record_to_row(
        record: dict[str, Any],
        display_index: int,
    ) -> dict[str, Any]:
        return {
            "序号": display_index,
            "内部记录ID": record.get("id", ""),
            "样本名称": record.get("sample_name", ""),
            "原图路径": record.get("image_path", ""),
            "掩膜路径": record.get("mask_path", ""),
            "叠加图路径": record.get("overlay_path", ""),
            "分析时间": record.get("analysis_time", ""),
            "图像宽度(px)": record.get("image_width", ""),
            "图像高度(px)": record.get("image_height", ""),
            "比例尺(cm/pixel)": record.get("cm_per_pixel", ""),
            "分割方法": record.get("segmentation_method", ""),
            "HSV下限": record.get("hsv_lower", ""),
            "HSV上限": record.get("hsv_upper", ""),
            "ExG阈值": record.get("exg_threshold", ""),
            "株高估算(px)": record.get("plant_height_px", ""),
            "株高估算(cm)": record.get("plant_height_cm", ""),
            "冠幅估算(px)": record.get("canopy_width_px", ""),
            "冠幅估算(cm)": record.get("canopy_width_cm", ""),
            "投影面积(px)": record.get("projected_area_px", ""),
            "投影面积(cm²)": record.get("projected_area_cm2", ""),
            "绿色覆盖率": record.get("green_coverage", ""),
            "ExG叶色指数均值": record.get("exg_mean", ""),
            "Green Ratio": record.get("green_ratio", ""),
            "外接矩形填充率": record.get("bbox_fill_ratio", ""),
            "长势评分": record.get("growth_score", ""),
            "备注": record.get("note", ""),
            "软件版本": record.get("software_version", ""),
        }

    @staticmethod
    def _batch_summary_to_rows(results: list[BatchItemResult]) -> list[dict[str, Any]]:
        summary = BatchStatisticsCalculator.calculate(results)

        rows = [
            {
                "统计类别": "基础统计",
                "统计项": "样本总数",
                "数值": summary.total_count,
                "单位": "张",
            },
            {
                "统计类别": "基础统计",
                "统计项": "成功数量",
                "数值": summary.success_count,
                "单位": "张",
            },
            {
                "统计类别": "基础统计",
                "统计项": "失败数量",
                "数值": summary.failed_count,
                "单位": "张",
            },
            {
                "统计类别": "基础统计",
                "统计项": "成功率",
                "数值": ResultExporter._format_percent_value(summary.success_rate),
                "单位": "%",
            },
        ]

        rows.extend(
            ResultExporter._metric_summary_rows(
                category="株高",
                stats=summary.plant_height_cm,
                unit="cm",
            )
        )
        rows.extend(
            ResultExporter._metric_summary_rows(
                category="冠幅",
                stats=summary.canopy_width_cm,
                unit="cm",
            )
        )
        rows.extend(
            ResultExporter._metric_summary_rows(
                category="投影面积",
                stats=summary.projected_area_cm2,
                unit="cm²",
            )
        )
        rows.extend(
            ResultExporter._metric_summary_rows(
                category="绿色覆盖率",
                stats=summary.green_coverage,
                unit="%",
                as_percent=True,
            )
        )
        rows.extend(
            ResultExporter._metric_summary_rows(
                category="长势评分",
                stats=summary.growth_score,
                unit="",
            )
        )

        return rows

    @staticmethod
    def _record_summary_to_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        total_count = len(records)

        rows = [
            {
                "统计类别": "基础统计",
                "统计项": "当前导出记录数",
                "数值": total_count,
                "单位": "条",
            }
        ]

        rows.extend(
            ResultExporter._value_summary_rows(
                records=records,
                key="plant_height_cm",
                category="株高",
                unit="cm",
            )
        )
        rows.extend(
            ResultExporter._value_summary_rows(
                records=records,
                key="canopy_width_cm",
                category="冠幅",
                unit="cm",
            )
        )
        rows.extend(
            ResultExporter._value_summary_rows(
                records=records,
                key="projected_area_cm2",
                category="投影面积",
                unit="cm²",
            )
        )
        rows.extend(
            ResultExporter._value_summary_rows(
                records=records,
                key="green_coverage",
                category="绿色覆盖率",
                unit="%",
                as_percent=True,
            )
        )
        rows.extend(
            ResultExporter._value_summary_rows(
                records=records,
                key="growth_score",
                category="长势评分",
                unit="",
            )
        )

        return rows

    @staticmethod
    def _metric_summary_rows(
        category: str,
        stats,
        unit: str,
        as_percent: bool = False,
    ) -> list[dict[str, Any]]:
        return [
            {
                "统计类别": category,
                "统计项": "均值",
                "数值": ResultExporter._format_summary_value(stats.mean_value, as_percent),
                "单位": unit,
            },
            {
                "统计类别": category,
                "统计项": "最小值",
                "数值": ResultExporter._format_summary_value(stats.min_value, as_percent),
                "单位": unit,
            },
            {
                "统计类别": category,
                "统计项": "最大值",
                "数值": ResultExporter._format_summary_value(stats.max_value, as_percent),
                "单位": unit,
            },
        ]

    @staticmethod
    def _value_summary_rows(
        records: list[dict[str, Any]],
        key: str,
        category: str,
        unit: str,
        as_percent: bool = False,
    ) -> list[dict[str, Any]]:
        values = ResultExporter._collect_float_values(records, key)

        if not values:
            mean_value = None
            min_value = None
            max_value = None
        else:
            mean_value = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)

        return [
            {
                "统计类别": category,
                "统计项": "均值",
                "数值": ResultExporter._format_summary_value(mean_value, as_percent),
                "单位": unit,
            },
            {
                "统计类别": category,
                "统计项": "最小值",
                "数值": ResultExporter._format_summary_value(min_value, as_percent),
                "单位": unit,
            },
            {
                "统计类别": category,
                "统计项": "最大值",
                "数值": ResultExporter._format_summary_value(max_value, as_percent),
                "单位": unit,
            },
        ]

    @staticmethod
    def _collect_float_values(records: list[dict[str, Any]], key: str) -> list[float]:
        values: list[float] = []

        for record in records:
            value = record.get(key)

            if value is None:
                continue

            try:
                values.append(float(value))
            except (TypeError, ValueError):
                continue

        return values

    @staticmethod
    def _format_summary_value(value, as_percent: bool = False) -> str:
        if value is None:
            return "-"

        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)

        if as_percent:
            return f"{number * 100:.2f}"

        return f"{number:.2f}"

    @staticmethod
    def _format_percent_value(value) -> str:
        try:
            return f"{float(value) * 100:.2f}"
        except (TypeError, ValueError):
            return "-"