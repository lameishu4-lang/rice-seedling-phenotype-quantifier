# -*- coding: utf-8 -*-

"""
SQLite 历史记录管理模块

本模块负责分析结果的本地存储、查询、备注更新和删除。
所有数据均保存在本地 SQLite 数据库中。
"""

import sqlite3
from pathlib import Path
from typing import Any

from rice_phenotype.utils.paths import database_path


class RecordRepository:
    """水稻秧苗图像表型分析记录仓库"""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or database_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.create_tables()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def create_tables(self) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    sample_name TEXT NOT NULL,
                    image_path TEXT NOT NULL,
                    mask_path TEXT,
                    overlay_path TEXT,

                    analysis_time TEXT NOT NULL,

                    image_width INTEGER,
                    image_height INTEGER,

                    cm_per_pixel REAL NOT NULL,

                    segmentation_method TEXT,
                    hsv_lower TEXT,
                    hsv_upper TEXT,
                    exg_threshold REAL,

                    plant_height_px REAL,
                    plant_height_cm REAL,
                    canopy_width_px REAL,
                    canopy_width_cm REAL,
                    projected_area_px REAL,
                    projected_area_cm2 REAL,
                    green_coverage REAL,
                    exg_mean REAL,
                    green_ratio REAL,
                    bbox_fill_ratio REAL,
                    growth_score REAL,

                    note TEXT,
                    software_version TEXT
                )
                """
            )

            conn.commit()

    def insert_record(self, record: dict[str, Any]) -> int:
        fields = [
            "sample_name",
            "image_path",
            "mask_path",
            "overlay_path",
            "analysis_time",
            "image_width",
            "image_height",
            "cm_per_pixel",
            "segmentation_method",
            "hsv_lower",
            "hsv_upper",
            "exg_threshold",
            "plant_height_px",
            "plant_height_cm",
            "canopy_width_px",
            "canopy_width_cm",
            "projected_area_px",
            "projected_area_cm2",
            "green_coverage",
            "exg_mean",
            "green_ratio",
            "bbox_fill_ratio",
            "growth_score",
            "note",
            "software_version",
        ]

        values = [record.get(field) for field in fields]

        placeholders = ", ".join(["?"] * len(fields))
        field_text = ", ".join(fields)

        sql = f"""
            INSERT INTO analysis_records ({field_text})
            VALUES ({placeholders})
        """

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
            return int(cursor.lastrowid)

    def query_records(
        self,
        keyword: str = "",
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        keyword = keyword.strip()

        with self._connect() as conn:
            cursor = conn.cursor()

            if keyword:
                cursor.execute(
                    """
                    SELECT *
                    FROM analysis_records
                    WHERE sample_name LIKE ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (f"%{keyword}%", limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT *
                    FROM analysis_records
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_record(self, record_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT *
                FROM analysis_records
                WHERE id = ?
                """,
                (record_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return dict(row)

    def update_note(self, record_id: int, note: str) -> bool:
        with self._connect() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE analysis_records
                SET note = ?
                WHERE id = ?
                """,
                (note, record_id),
            )

            conn.commit()
            return cursor.rowcount > 0

    def delete_record(self, record_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM analysis_records
                WHERE id = ?
                """,
                (record_id,),
            )

            conn.commit()
            return cursor.rowcount > 0