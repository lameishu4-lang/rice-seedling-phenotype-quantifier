# -*- coding: utf-8 -*-

"""
软件参数设置模块

本模块负责保存和读取水稻秧苗图像表型量化软件的全局参数。
参数以 JSON 文件形式保存在本地 data/settings.json 中。

本模块不涉及 AI、深度学习或外部接口，仅保存传统图像处理参数。
"""

from dataclasses import dataclass, asdict
from pathlib import Path
import json

from rice_phenotype.utils.paths import data_dir


@dataclass
class AppSettings:
    segmentation_method: str = "HSV"

    hsv_h_min: int = 35
    hsv_s_min: int = 40
    hsv_v_min: int = 40

    hsv_h_max: int = 85
    hsv_s_max: int = 255
    hsv_v_max: int = 255

    exg_threshold: int = 30
    min_area: int = 300
    kernel_size: int = 5

    default_cm_per_pixel: float = 0.05000


class SettingsManager:
    """全局设置读写工具"""

    def __init__(self, settings_path: Path | None = None):
        self.settings_path = settings_path or data_dir() / "settings.json"

    def load(self) -> AppSettings:
        if not self.settings_path.exists():
            return AppSettings()

        try:
            with self.settings_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            default = AppSettings()
            default_dict = asdict(default)
            default_dict.update(data)

            return AppSettings(**default_dict)

        except Exception:
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)

        with self.settings_path.open("w", encoding="utf-8") as f:
            json.dump(asdict(settings), f, ensure_ascii=False, indent=2)

    def reset(self) -> AppSettings:
        settings = AppSettings()
        self.save(settings)
        return settings