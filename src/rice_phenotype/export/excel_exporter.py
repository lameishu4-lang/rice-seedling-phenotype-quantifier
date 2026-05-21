# -*- coding: utf-8 -*-

"""
Excel / CSV 导出模块

本模块负责将批量分析结果或历史记录导出为 Excel / CSV 文件。
"""

from pathlib import Path
from typing import Any

import pandas as pd

from rice_phenotype.core.batch import BatchItemResult


class ResultExporter:
    """分析结果导出工具"""

    @staticmethod
    def export_batch_results_to_excel(
        results: list[BatchItemResult],
        output_path: Path,
    ) -> Path:
        rows = ResultExporter._batch_results_to_rows(results)
        df = pd.DataFrame(rows)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(output_path, index=False)
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
        rows = [ResultExporter._record_to_row(record) for record in records]
        df = pd.DataFrame(rows)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(output_path, index=False)
        return output_path

    @staticmethod
    def export_records_to_csv(
        records: list[dict[str, Any]],
        output_path: Path,
    ) -> Path:
        rows = [ResultExporter._record_to_row(record) for record in records]
        df = pd.DataFrame(rows)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        return output_path

    @staticmethod
    def _batch_results_to_rows(results: list[BatchItemResult]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []

        for index, item in enumerate(results, start=1):
            metrics = item.metrics

            row = {
                "序号": index,
                "样本名称": item.sample_name,
                "图像路径": str(item.image_path),
                "分析状态": "成功" if item.success else "失败",
                "信息": item.message,
                "图像宽度(px)": item.image_width,
                "图像高度(px)": item.image_height,
                "秧苗掩膜面积(px)": item.plant_area_px,
                "外接矩形": str(item.bbox) if item.bbox else "",
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
    def _record_to_row(record: dict[str, Any]) -> dict[str, Any]:
        return {
            "记录ID": record.get("id", ""),
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